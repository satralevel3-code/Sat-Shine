from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Case, When
from django.db import transaction
from datetime import datetime, timedelta, date, time
from .models import CustomUser, Attendance, LeaveRequest, TravelRequest
import json

@login_required
def associate_dashboard(request):
    """Associate dashboard with travel request management"""
    if request.user.designation != 'Associate':
        messages.error(request, 'Access denied. Associate privileges required.')
        return redirect('field_dashboard')
    
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
    
    # Get travel request filters
    from_date = request.GET.get('from_date', timezone.localdate().isoformat())
    to_date = request.GET.get('to_date', (timezone.localdate() + timedelta(days=30)).isoformat())
    employee_id = request.GET.get('employee_id', '')
    designation = request.GET.get('designation', '')
    duration = request.GET.get('duration', '')
    status = request.GET.get('status', '')
    
    # Get travel requests for Associate's DCCBs
    travel_requests = TravelRequest.objects.filter(
        request_to=request.user,
        from_date__range=[from_date, to_date]
    ).select_related('user')
    
    # Apply filters
    if employee_id:
        travel_requests = travel_requests.filter(user__employee_id__icontains=employee_id)
    if designation:
        travel_requests = travel_requests.filter(user__designation=designation)
    if duration:
        travel_requests = travel_requests.filter(duration=duration)
    if status:
        travel_requests = travel_requests.filter(status=status)
    
    # Order by status (pending first)
    travel_requests = travel_requests.order_by(
        Case(
            When(status='pending', then=0),
            When(status='approved', then=1),
            When(status='rejected', then=2),
            default=3
        ),
        '-created_at'
    )
    
    # Count pending travel requests
    pending_travel_requests = travel_requests.filter(status='pending').count()
    
    context = {
        'user': request.user,
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'pending_leaves': pending_leaves,
        'pending_travel_requests': pending_travel_requests,
        'travel_requests': travel_requests,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id': employee_id,
        'designation': designation,
        'duration': duration,
        'status': status,
        'current_time': timezone.now(),
    }
    
    return render(request, 'authe/associate_dashboard.html', context)

@login_required
def associate_mark_attendance(request):
    """Enhanced attendance marking for Associates"""
    if request.user.designation != 'Associate':
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')  # 'check_in', 'half_day', 'absent', 'check_out'
            
            today = timezone.localdate()
            current_time = timezone.localtime().time()
            
            # Check if attendance already exists
            attendance, created = Attendance.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={'status': 'absent', 'marked_at': timezone.now()}
            )
            
            if action == 'absent':
                attendance.status = 'absent'
                attendance.check_in_time = None
                attendance.check_out_time = None
                attendance.workplace = None
                attendance.task = None
                attendance.travel_reason = None
                attendance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Marked as absent successfully'
                })
            
            elif action in ['check_in', 'half_day']:
                # Validate required fields
                workplace = data.get('workplace')
                task = data.get('task', '')
                travel_required = data.get('travel_required')
                travel_reason = data.get('travel_reason', '')
                
                if not workplace:
                    return JsonResponse({
                        'success': False,
                        'error': 'Workplace is required'
                    })
                
                # Check if travel is required but no reason given when no approved travel
                approved_travel_today = TravelRequest.objects.filter(
                    user=request.user,
                    from_date__lte=today,
                    to_date__gte=today,
                    status='approved'
                ).exists()
                
                if travel_required == 'no' and approved_travel_today and not travel_reason:
                    return JsonResponse({
                        'success': False,
                        'error': 'Travel reason is required when declining approved travel'
                    })
                
                # Update attendance
                attendance.status = 'present' if action == 'check_in' else 'half_day'
                attendance.check_in_time = current_time
                attendance.workplace = workplace
                attendance.task = task
                attendance.travel_required = travel_required == 'yes'
                attendance.travel_reason = travel_reason
                
                # Capture GPS location (placeholder - implement GPS capture)
                attendance.latitude = data.get('latitude')
                attendance.longitude = data.get('longitude')
                attendance.location_accuracy = data.get('accuracy')
                attendance.location_address = data.get('address', '')
                
                attendance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Attendance marked as {attendance.get_status_display()} successfully'
                })
            
            elif action == 'check_out':
                if not attendance or attendance.status == 'absent':
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot check out without checking in first'
                    })
                
                # Check if it's after 2:30 PM
                if current_time < time(14, 30):
                    return JsonResponse({
                        'success': False,
                        'error': 'Check out is only available after 2:30 PM'
                    })
                
                attendance.check_out_time = current_time
                attendance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Checked out successfully'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_attendance_status(request):
    """Get current attendance status for Associate"""
    if request.user.designation != 'Associate':
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    today = timezone.localdate()
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    # Check approved travel for today
    approved_travel_today = TravelRequest.objects.filter(
        user=request.user,
        from_date__lte=today,
        to_date__gte=today,
        status='approved'
    ).exists()
    
    current_time = timezone.localtime().time()
    can_check_out = current_time >= time(14, 30)
    
    return JsonResponse({
        'success': True,
        'attendance': {
            'status': attendance.status if attendance else None,
            'check_in_time': attendance.check_in_time.strftime('%H:%M') if attendance and attendance.check_in_time else None,
            'check_out_time': attendance.check_out_time.strftime('%H:%M') if attendance and attendance.check_out_time else None,
            'workplace': attendance.workplace if attendance else None,
        },
        'approved_travel_today': approved_travel_today,
        'can_check_out': can_check_out,
        'current_time': current_time.strftime('%H:%M')
    })

@login_required
def travel_request_details(request, request_id):
    """Get travel request details for modal display"""
    # Allow Associates and Admin users
    if request.user.designation != 'Associate' and request.user.role_level < 10:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        # For Associates, only show requests assigned to them
        # For Admins, show all requests
        if request.user.designation == 'Associate':
            travel_request = TravelRequest.objects.select_related('user').get(
                id=request_id,
                request_to=request.user
            )
        else:
            travel_request = TravelRequest.objects.select_related('user').get(id=request_id)
        
        return JsonResponse({
            'success': True,
            'request': {
                'employee_id': travel_request.user.employee_id,
                'user_name': f"{travel_request.user.first_name} {travel_request.user.last_name}",
                'user_dccb': travel_request.user.dccb,
                'designation': travel_request.user.designation,
                'from_date': travel_request.from_date.strftime('%d %b %Y'),
                'to_date': travel_request.to_date.strftime('%d %b %Y'),
                'duration': travel_request.get_duration_display(),
                'days_count': travel_request.days_count,
                'er_id': travel_request.er_id,
                'distance_km': travel_request.distance_km,
                'address': travel_request.address,
                'contact_person': travel_request.contact_person,
                'purpose': travel_request.purpose,
                'status': travel_request.get_status_display(),
                'created_at': travel_request.created_at.strftime('%d %b %Y, %I:%M %p'),
            }
        })
        
    except TravelRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Travel request not found'})