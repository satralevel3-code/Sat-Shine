from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, time
from .models import CustomUser, Attendance, LeaveRequest
from .views import create_audit_log
import json
import os

# Conditional GIS imports
if os.getenv('USE_POSTGRESQL', 'false').lower() == 'true':
    try:
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import Distance
        GIS_ENABLED = True
    except ImportError:
        GIS_ENABLED = False
else:
    GIS_ENABLED = False

@login_required
def field_dashboard(request):
    """Main dashboard for field officers - role-based access"""
    if request.user.role != 'field_officer':
        messages.error(request, 'Access denied. Field Officer privileges required.')
        return redirect('admin_dashboard')
    
    # Clear all messages on dashboard load to prevent persistence
    storage = messages.get_messages(request)
    storage.used = True
    
    # Get today's attendance
    today = timezone.localdate()
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    # Get recent attendance (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_attendance = Attendance.objects.filter(
        user=request.user, 
        date__gte=week_ago
    ).order_by('-date')[:7]
    
    # Get pending leave requests
    pending_leaves = LeaveRequest.objects.filter(
        user=request.user, 
        status='pending'
    ).count()
    
    # Get recent leave requests for display
    recent_leaves = LeaveRequest.objects.filter(
        user=request.user
    ).order_by('-applied_at')[:5]
    
    # Check if user can view team data (DC only)
    can_view_team = request.user.designation == 'DC'
    team_data = None
    team_members = []  # Initialize team_members
    
    if can_view_team:
        # Get team attendance for DC
        team_users = CustomUser.objects.filter(
            role='field_officer',
            dccb=request.user.dccb,
            designation__in=['MT', 'Support']
        ).exclude(id=request.user.id).order_by('employee_id')
        
        # Get today's attendance for team members
        team_members = []
        for user in team_users:
            user_attendance = Attendance.objects.filter(user=user, date=today).first()
            user.today_attendance = user_attendance
            team_members.append(user)
        
        team_attendance_today = Attendance.objects.filter(
            user__in=team_users,
            date=today
        ).values('status').annotate(count=Count('status'))
        
        team_data = {
            'total_team': team_users.count(),
            'attendance_summary': {item['status']: item['count'] for item in team_attendance_today}
        }
    
    context = {
        'user': request.user,
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'pending_leaves': pending_leaves,
        'recent_leaves': recent_leaves,
        'can_view_team': can_view_team,
        'team_data': team_data,
        'team_members': team_members,
        'current_time': timezone.now(),
    }
    
    return render(request, 'authe/field_dashboard.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST", "GET"])
def mark_attendance(request):
    """Production-ready attendance marking with high-accuracy GPS validation"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.localdate()
    is_sunday_today = today.weekday() == 6
    
    if request.method == 'POST':
        if is_sunday_today:
            return JsonResponse({
                'success': False, 
                'error': 'Attendance marking not allowed on Sundays'
            }, status=400)
            
        try:
            data = json.loads(request.body)
            latitude = data.get('lat')
            longitude = data.get('lng')
            accuracy = data.get('accuracy')
            timestamp = data.get('timestamp')
            
            current_time = timezone.localtime().time()
            
            # Check if already marked
            existing = Attendance.objects.filter(user=request.user, date=today).first()
            if existing:
                return JsonResponse({'success': False, 'error': 'Attendance already marked for today'}, status=400)
            
            # Strict GPS validation for production
            if latitude is None or longitude is None or accuracy is None:
                return JsonResponse({'success': False, 'error': 'GPS location data required'}, status=400)
            
            try:
                lat_float = float(latitude)
                lng_float = float(longitude)
                acc_float = float(accuracy)
                
                # Validate coordinate ranges
                if not (-90 <= lat_float <= 90 and -180 <= lng_float <= 180):
                    return JsonResponse({'success': False, 'error': 'Invalid GPS coordinates'}, status=400)
                
                # Strict accuracy requirement: ≤50 meters
                if acc_float > 50:
                    return JsonResponse({
                        'success': False, 
                        'error': f'GPS accuracy too low ({acc_float:.1f}m). Required: ≤50m. Please move to an open area and try again.'
                    }, status=400)
                    
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid location data format'}, status=400)
            
            # Office geofencing (optional - Ahmedabad office coordinates)
            office_lat = 23.0225
            office_lng = 72.5714
            office_radius = 200  # 200 meters
            
            # Calculate distance from office (simple approximation)
            import math
            lat_diff = lat_float - office_lat
            lng_diff = lng_float - office_lng
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111000  # Convert to meters
            
            is_within_office = distance <= office_radius
            
            # Time-based status determination
            on_time_cutoff = time(10, 0)
            late_cutoff = time(13, 30)
            half_day_cutoff = time(15, 0)
            
            if current_time <= on_time_cutoff:
                status = 'present'
                timing_status = 'On Time'
                message = 'Attendance marked successfully - On Time'
            elif current_time <= late_cutoff:
                status = 'present'
                timing_status = 'Late Arrival'
                message = f'Marked late at {current_time.strftime("%I:%M %p")}'
            elif current_time <= half_day_cutoff:
                status = 'half_day'
                timing_status = 'Half Day'
                message = f'Marked as Half Day at {current_time.strftime("%I:%M %p")}'
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Attendance marking not allowed after 3:00 PM. Current time: {current_time.strftime("%I:%M %p")}'
                }, status=400)
            
            # Create attendance record with validation flags
            attendance = Attendance.objects.create(
                user=request.user,
                date=today,
                status=status,
                check_in_time=current_time,
                check_in_location=f"{lat_float:.8f},{lng_float:.8f}",
                location_accuracy=acc_float,
                is_location_valid=True,  # Always true since we validated accuracy ≤50m
                location_address=f'GPS: {acc_float:.1f}m accuracy' + (' (Office)' if is_within_office else ' (Remote)'),
                distance_from_office=distance
            )
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='ATTENDANCE_MARKED',
                details=f'Status: {status}, Time: {current_time}, Location: {lat_float:.6f},{lng_float:.6f}, Accuracy: {acc_float:.1f}m, Distance: {distance:.0f}m'
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'status': status,
                'timing_status': timing_status,
                'check_in_time': current_time.strftime('%I:%M %p'),
                'location': f'{lat_float:.6f},{lng_float:.6f}',
                'accuracy': f'{acc_float:.1f}m',
                'office_distance': f'{distance:.0f}m',
                'within_office': is_within_office
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
    
    # GET request - return attendance form
    context = {
        'user': request.user,
        'today': today,
        'is_sunday': is_sunday_today,
        'current_time': timezone.now()
    }
    return render(request, 'authe/mark_attendance.html', context)

@login_required
def attendance_history(request):
    """Display attendance history for field officers"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get attendance records for the user
    attendance_records = Attendance.objects.filter(
        user=request.user
    ).order_by('-date')[:30]  # Last 30 records
    
    context = {
        'user': request.user,
        'attendance_records': attendance_records,
    }
    return render(request, 'authe/attendance_history.html', context)

@login_required
def attendance_summary(request):
    """Get attendance summary data for field officers"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.localdate()
    current_month = today.replace(day=1)
    
    # Get monthly attendance stats
    monthly_attendance = Attendance.objects.filter(
        user=request.user,
        date__gte=current_month
    )
    
    present_count = monthly_attendance.filter(status='present').count()
    absent_count = monthly_attendance.filter(status='absent').count()
    half_day_count = monthly_attendance.filter(status='half_day').count()
    
    return JsonResponse({
        'present': present_count,
        'absent': absent_count,
        'half_day': half_day_count,
        'total_marked': present_count + absent_count + half_day_count
    })

@login_required
@csrf_exempt
@require_http_methods(["POST", "GET"])
def apply_leave(request):
    """Apply for leave - field officers"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            leave_type = data.get('leave_type')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            reason = data.get('reason', '')
            
            # Validate dates
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
            
            if start_date > end_date:
                return JsonResponse({'success': False, 'error': 'Start date cannot be after end date'}, status=400)
            
            # Create leave request
            leave_request = LeaveRequest.objects.create(
                user=request.user,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                status='pending'
            )
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='LEAVE_APPLIED',
                details=f'Type: {leave_type}, Dates: {start_date} to {end_date}, Reason: {reason}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Leave application submitted successfully',
                'leave_id': leave_request.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
    
    # GET request - return leave application form
    context = {
        'user': request.user,
        'leave_types': LeaveRequest.LEAVE_TYPE_CHOICES,
    }
    return render(request, 'authe/apply_leave.html', context)