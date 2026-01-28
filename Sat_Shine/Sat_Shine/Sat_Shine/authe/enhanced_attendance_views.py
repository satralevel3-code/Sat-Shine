from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, time
from .models import CustomUser, Attendance, TravelRequest
from .enterprise_permissions import log_enterprise_action
import json
import math

@login_required
@csrf_exempt
def enhanced_mark_attendance(request):
    """Enhanced attendance marking with check-in/check-out workflow"""
    if request.user.role not in ['field_officer', 'dc', 'mt', 'support', 'associate']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.localdate()
    current_time = timezone.localtime().time()
    
    # Get today's attendance record
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action', 'check_in')
            
            if action == 'check_out':
                return handle_check_out(request, today_attendance, data)
            else:
                return handle_check_in(request, data, today, current_time)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - show attendance marking interface
    travel_approved = TravelRequest.objects.filter(
        user=request.user,
        from_date__lte=today,
        to_date__gte=today,
        status='approved'
    ).exists()
    
    context = {
        'user': request.user,
        'today': today,
        'today_attendance': today_attendance,
        'current_time': timezone.now(),
        'travel_approved': travel_approved,
        'workplace_choices': CustomUser.WORKPLACE_CHOICES,
        'can_check_out': current_time >= time(18, 0) and current_time <= time(23, 0)
    }
    
    return render(request, 'authe/enhanced_mark_attendance.html', context)

def handle_check_in(request, data, today, current_time):
    """Handle check-in process with enhanced validation"""
    
    # Check if already checked in
    existing = Attendance.objects.filter(user=request.user, date=today).first()
    if existing:
        return JsonResponse({'success': False, 'error': 'Already checked in today'}, status=400)
    
    status = data.get('status')
    travel_required = data.get('travel_required', False)
    workplace = data.get('workplace')
    travel_reason = data.get('travel_reason', '')
    task = data.get('task', '')
    
    # Validate required fields for present/half_day
    if status in ['present', 'half_day']:
        if not workplace:
            return JsonResponse({'success': False, 'error': 'Workplace is required'}, status=400)
        
        # Check travel approval requirement
        travel_approved = TravelRequest.objects.filter(
            user=request.user,
            from_date__lte=today,
            to_date__gte=today,
            status='approved'
        ).exists()
        
        if travel_required and not travel_approved:
            return JsonResponse({'success': False, 'error': 'Travel not approved for today'}, status=400)
        
        if not travel_required and not travel_approved and not travel_reason.strip():
            return JsonResponse({'success': False, 'error': 'Travel reason required when travel not approved'}, status=400)
    
    # Determine time status based on check-in time
    time_status = 'on_time'
    if current_time > time(10, 0) and current_time <= time(14, 30):
        time_status = 'late'
    elif current_time > time(14, 30):
        status = 'half_day'  # Force half day for late check-in
        time_status = 'half_day_late'
    
    # Get GPS location for present/half_day
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy')
    
    location_data = {}
    if status != 'absent' and latitude and longitude:
        location_data = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'location_accuracy': float(accuracy) if accuracy else 999,
            'is_location_valid': True,
            'location_address': f'GPS: {accuracy}m accuracy' if accuracy else 'GPS Location'
        }
    
    # Create attendance record
    attendance = Attendance.objects.create(
        user=request.user,
        date=today,
        status=status,
        check_in_time=current_time,
        time_status=time_status,
        travel_required=travel_required,
        travel_approved=travel_approved,
        workplace=workplace,
        task=task,
        travel_reason=travel_reason,
        **location_data
    )
    
    # Enterprise audit logging
    log_enterprise_action(
        user=request.user,
        action_type='ATTENDANCE_CHECKED_IN',
        target_table='attendance',
        target_id=attendance.id,
        new_value={
            'status': status,
            'time_status': time_status,
            'workplace': workplace
        },
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Checked in as {status.replace("_", " ").title()}',
        'check_in_time': current_time.strftime('%I:%M %p'),
        'status': status,
        'time_status': time_status
    })

def handle_check_out(request, attendance_record, data):
    """Handle check-out process"""
    
    if not attendance_record:
        return JsonResponse({'success': False, 'error': 'No check-in record found'}, status=400)
    
    if attendance_record.check_out_time:
        return JsonResponse({'success': False, 'error': 'Already checked out'}, status=400)
    
    current_time = timezone.localtime().time()
    
    # Validate check-out time window (6:00 PM to 11:00 PM)
    if not (time(18, 0) <= current_time <= time(23, 0)):
        return JsonResponse({'success': False, 'error': 'Check-out allowed only between 6:00 PM and 11:00 PM'}, status=400)
    
    # Get GPS location for check-out
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Update attendance record
    attendance_record.check_out_time = current_time
    
    if latitude and longitude:
        # Store check-out location in remarks
        checkout_location = f"Check-out location: {latitude}, {longitude}"
        if attendance_record.remarks:
            attendance_record.remarks += f"\n{checkout_location}"
        else:
            attendance_record.remarks = checkout_location
    
    attendance_record.save()
    
    # Enterprise audit logging
    log_enterprise_action(
        user=request.user,
        action_type='ATTENDANCE_CHECKED_OUT',
        target_table='attendance',
        target_id=attendance_record.id,
        new_value={
            'check_out_time': current_time.strftime('%H:%M:%S'),
            'location': f"{latitude},{longitude}" if latitude else None
        },
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Checked out successfully',
        'check_out_time': current_time.strftime('%I:%M %p')
    })

@login_required
def dc_team_overview(request):
    """DC Team Overview with confirmation functionality"""
    if request.user.designation != 'DC':
        messages.error(request, 'DC privileges required')
        return redirect('field_dashboard')
    
    # Date range filter
    start_date = request.GET.get('start_date', timezone.localdate().strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.localdate().strftime('%Y-%m-%d'))
    
    # Get team members
    team_members = CustomUser.objects.filter(
        role='field_officer',
        dccb=request.user.dccb,
        designation__in=['MT', 'Support'],
        is_active=True
    ).order_by('employee_id')
    
    # Get attendance records for date range
    attendance_records = Attendance.objects.filter(
        user__in=team_members,
        date__range=[start_date, end_date]
    ).select_related('user').order_by('-date', 'user__employee_id')
    
    context = {
        'user': request.user,
        'team_members': team_members,
        'attendance_records': attendance_records,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'authe/dc_team_overview.html', context)

@login_required
@csrf_exempt
def dc_confirm_attendance(request):
    """DC Attendance Confirmation with auto-absent for unmarked"""
    if request.user.designation != 'DC':
        return JsonResponse({'error': 'DC privileges required'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
            
            # Get team members
            team_members = CustomUser.objects.filter(
                role='field_officer',
                dccb=request.user.dccb,
                designation__in=['MT', 'Support'],
                is_active=True
            )
            
            confirmed_count = 0
            created_count = 0
            
            # Process each date in range
            current_date = start_date
            while current_date <= end_date:
                # Skip Sundays
                if current_date.weekday() != 6:
                    for member in team_members:
                        attendance, created = Attendance.objects.get_or_create(
                            user=member,
                            date=current_date,
                            defaults={
                                'status': 'absent',  # Auto-absent for unmarked
                                'is_confirmed_by_dc': True,
                                'confirmed_by_dc': request.user,
                                'dc_confirmed_at': timezone.now()
                            }
                        )
                        
                        if created:
                            created_count += 1
                        elif not attendance.is_confirmed_by_dc:
                            attendance.is_confirmed_by_dc = True
                            attendance.confirmed_by_dc = request.user
                            attendance.dc_confirmed_at = timezone.now()
                            attendance.save()
                            confirmed_count += 1
                
                current_date += timedelta(days=1)
            
            return JsonResponse({
                'success': True,
                'message': f'Confirmed {confirmed_count} records, Created {created_count} absent records',
                'confirmed_count': confirmed_count,
                'created_count': created_count
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST method required'}, status=405)