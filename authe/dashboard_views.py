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
            
            current_time = timezone.localtime().time()
            
            # Check if already marked
            existing = Attendance.objects.filter(user=request.user, date=today).first()
            if existing:
                return JsonResponse({'success': False, 'error': 'Attendance already marked for today'}, status=400)
            
            # Validate GPS data
            if latitude is None or longitude is None or accuracy is None:
                return JsonResponse({'success': False, 'error': 'GPS location required'}, status=400)
            
            try:
                lat_float = float(latitude)
                lng_float = float(longitude)
                acc_float = float(accuracy)
                
                if not (-90 <= lat_float <= 90 and -180 <= lng_float <= 180):
                    return JsonResponse({'success': False, 'error': 'Invalid GPS coordinates'}, status=400)
                
                if acc_float > 50:
                    return JsonResponse({
                        'success': False, 
                        'error': f'GPS accuracy too low ({acc_float:.0f}m). Required: ≤50m'
                    }, status=400)
                    
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid location data'}, status=400)
            
            # Time-based attendance rules
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
                message = f'Marked late at {current_time.strftime("%I:%M %p")} - Late Arrival'
            elif current_time <= half_day_cutoff:
                status = 'half_day'
                timing_status = 'Half Day'
                message = f'Marked at {current_time.strftime("%I:%M %p")} - Half Day'
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Attendance marking not allowed after 3:00 PM. Current time: {current_time.strftime("%I:%M %p")}'
                }, status=400)
            
            # Create attendance record
            attendance = Attendance.objects.create(
                user=request.user,
                date=today,
                status=status,
                check_in_time=current_time,
                check_in_location=f"{lat_float:.8f},{lng_float:.8f}",
                location_accuracy=acc_float,
                is_location_valid=True,
                location_address='GPS Location Captured'
            )
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='ATTENDANCE_MARKED',
                details=f'Status: {status}, Time: {current_time}, Location: {lat_float:.6f},{lng_float:.6f}'
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'status': status,
                'timing_status': timing_status,
                'check_in_time': current_time.strftime('%I:%M %p'),
                'location': f'{lat_float:.6f},{lng_float:.6f}',
                'accuracy': f'{acc_float:.1f}m'
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