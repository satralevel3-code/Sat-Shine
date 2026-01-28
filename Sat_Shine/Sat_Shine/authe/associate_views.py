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
def associate_mark_attendance_page(request):
    """Associate mark attendance page"""
    return render(request, 'authe/associate_mark_attendance.html')

@login_required
def associate_dashboard(request):
    """Associate dashboard with travel request management"""
    # Allow both Associates and Admin users to access
    if request.user.designation != 'Associate' and request.user.role_level < 10:
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
    
    # Get travel request filters - Use wider date range to show past and future requests
    from_date = request.GET.get('from_date', (timezone.localdate() - timedelta(days=30)).isoformat())
    to_date = request.GET.get('to_date', (timezone.localdate() + timedelta(days=60)).isoformat())
    employee_id = request.GET.get('employee_id', '')
    designation = request.GET.get('designation', '')
    duration = request.GET.get('duration', '')
    status = request.GET.get('status', '')
    
    # Get travel requests based on user type
    if request.user.designation == 'Associate':
        # For Associates: show ALL travel requests from MT/DC/Support users (no DCCB restriction)
        travel_requests = TravelRequest.objects.filter(
            user__designation__in=['MT', 'DC', 'Support'],
            from_date__range=[from_date, to_date]
        ).select_related('user')
    else:
        # For Admins: show all travel requests
        travel_requests = TravelRequest.objects.filter(
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
    """Simple Associate attendance marking - Present/Half Day/Absent with GPS auto-fetch"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')  # 'present', 'half_day', 'absent'
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            # Validate status
            if status not in ['present', 'half_day', 'absent']:
                return JsonResponse({'success': False, 'error': 'Invalid status'})
            
            today = timezone.localdate()
            
            # Check if attendance already marked
            existing_attendance = Attendance.objects.filter(
                user=request.user,
                date=today
            ).first()
            
            if existing_attendance:
                return JsonResponse({
                    'success': False, 
                    'error': 'Attendance already marked for today'
                })
            
            # Create attendance record
            attendance = Attendance.objects.create(
                user=request.user,
                date=today,
                status=status,
                latitude=latitude if status != 'absent' else None,
                longitude=longitude if status != 'absent' else None,
                check_in_time=timezone.localtime().time() if status != 'absent' else None,
                marked_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Attendance marked as {status.title()}'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_attendance_status(request):
    """Get current attendance status for Associate"""
    today = timezone.localdate()
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    return JsonResponse({
        'success': True,
        'attendance': {
            'status': attendance.status if attendance else None,
            'check_in_time': attendance.check_in_time.strftime('%H:%M') if attendance and attendance.check_in_time else None,
        },
        'current_time': timezone.localtime().time().strftime('%H:%M')
    })

@login_required
def travel_request_details(request, request_id):
    """Get travel request details for modal display"""
    # Allow Associates and Admin users
    if request.user.designation != 'Associate' and request.user.role_level < 10:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        # For Associates, show all travel requests from MT/DC/Support users
        # For Admins, show all requests
        if request.user.designation == 'Associate':
            travel_request = TravelRequest.objects.select_related('user').get(
                id=request_id,
                user__designation__in=['MT', 'DC', 'Support']
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