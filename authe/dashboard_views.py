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
import math

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
@require_http_methods(["POST", "GET"])
def mark_attendance(request):
    """Simplified attendance marking"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.localdate()
    
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except:
                return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        else:
            data = request.POST
            
        status = data.get('status')
        latitude = data.get('lat')
        longitude = data.get('lng')
        accuracy = data.get('accuracy')
        
        # Check if already marked
        existing = Attendance.objects.filter(user=request.user, date=today).first()
        if existing:
            messages.error(request, 'Attendance already marked for today')
            return redirect('mark_attendance')
        
        # Validate status
        if status not in ['present', 'half_day', 'absent']:
            messages.error(request, 'Invalid attendance status')
            return redirect('mark_attendance')
        
        current_time = timezone.localtime().time()
        
        # Create attendance record
        try:
            attendance_data = {
                'user': request.user,
                'date': today,
                'status': status,
                'check_in_time': current_time,
            }
            
            # Add GPS data if available
            if latitude and longitude and status != 'absent':
                accuracy = float(accuracy) if accuracy else 999
                
                # Backend validation - reject poor accuracy
                if accuracy > 200:
                    messages.error(request, 'Location not available. Please try again.')
                    return redirect('mark_attendance')
                
                attendance_data.update({
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'location_accuracy': accuracy,
                    'is_location_valid': True,
                    'location_address': f'GPS Location',
                    'distance_from_office': 0
                })
            
            attendance = Attendance.objects.create(**attendance_data)
            
            # Success message
            messages.success(request, f'Attendance marked as {status.replace("_", " ").title()} at {current_time.strftime("%I:%M %p")}')
            
            # Return JSON for AJAX or redirect for form
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'Marked {status}',
                    'check_in_time': current_time.strftime('%I:%M %p')
                })
            else:
                return redirect('field_dashboard')
                
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            else:
                return redirect('mark_attendance')
    
    # GET request
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    context = {
        'user': request.user,
        'today': today,
        'today_attendance': today_attendance,
        'current_time': timezone.now()
    }
    return render(request, 'authe/mark_attendance_simple.html', context)

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