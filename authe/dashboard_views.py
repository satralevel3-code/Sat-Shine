from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, time
from .models import CustomUser, Attendance, LeaveRequest, AttendanceAuditLog, TravelRequest, SystemAuditLog
from .views import create_audit_log
from .enterprise_permissions import check_hierarchy_permission, log_enterprise_action
import json
import math

@login_required
def field_dashboard(request):
    """Main dashboard for field officers - role-based access"""
    if request.user.role != 'field_officer':
        messages.error(request, 'Access denied. Field Officer privileges required.')
        return redirect('admin_dashboard')
    
    # Get today's attendance - include all records for this user today
    today = timezone.localdate()
    today_attendance = Attendance.objects.filter(
        user=request.user, 
        date=today
    ).first()
    
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
    
    # Get pending travel requests (for MT, DC, Support)
    pending_travel_requests = 0
    if request.user.designation in ['MT', 'DC', 'Support']:
        pending_travel_requests = TravelRequest.objects.filter(
            user=request.user,
            status='pending'
        ).count()
    
    # Check if user can view team data (DC only)
    can_view_team = request.user.designation == 'DC'
    team_data = None
    team_members = []  # Initialize team_members
    pending_dc_confirmations = 0  # Counter for pending DC confirmations
    
    if can_view_team:
        # Get team attendance for DC - ONLY MT and Support
        team_users = CustomUser.objects.filter(
            role='field_officer',
            dccb=request.user.dccb,
            designation__in=['MT', 'Support']
        ).exclude(id=request.user.id).order_by('employee_id')
        
        # Get today's attendance for team members - include DC confirmed records
        team_members = []
        for user in team_users:
            user_attendance = Attendance.objects.filter(user=user, date=today).first()
            user.today_attendance = user_attendance
            team_members.append(user)
        
        team_attendance_today = Attendance.objects.filter(
            user__in=team_users,
            date=today
        ).values('status').annotate(count=Count('status'))
        
        # Count ONLY MT/Support pending DC confirmations (exclude Associates and DCs)
        pending_dc_confirmations = Attendance.objects.filter(
            user__designation__in=['MT', 'Support'],
            user__dccb=request.user.dccb,
            is_confirmed_by_dc=False,
            status__in=['present', 'half_day']
        ).exclude(user=request.user).count()
        
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
        'pending_travel_requests': pending_travel_requests,
        'can_view_team': can_view_team,
        'team_data': team_data,
        'team_members': team_members,
        'pending_dc_confirmations': pending_dc_confirmations,
        'current_time': timezone.now(),
    }
    
    return render(request, 'authe/field_dashboard.html', context)

@login_required
@require_http_methods(["POST", "GET"])
def mark_attendance(request):
    """Enhanced attendance marking with check-in/check-out flow"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Only allow MT, DC, Support designations
    if request.user.designation not in ['MT', 'DC', 'Support']:
        messages.error(request, 'Attendance marking is only available for MT, DC, and Support designations.')
        return redirect('field_dashboard')
    
    today = timezone.localdate()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            workplace = data.get('workplace')
            travel_required = data.get('travel_required', False)
            travel_comment = data.get('travel_comment', '')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            accuracy = data.get('accuracy')
            
            # Check if already marked
            existing = Attendance.objects.filter(user=request.user, date=today).first()
            if existing:
                return JsonResponse({'success': False, 'error': 'Attendance already marked for today'}, status=400)
            
            # Validate status
            if status not in ['present', 'half_day', 'absent']:
                return JsonResponse({'success': False, 'error': 'Invalid attendance status'}, status=400)
            
            current_time = timezone.localtime().time()
            
            # Create attendance record
            attendance_data = {
                'user': request.user,
                'date': today,
                'status': status,
                'check_in_time': current_time if status != 'absent' else None,
                'workplace': workplace if status != 'absent' else None,
                'travel_required': travel_required if status != 'absent' else False,
            }
            
            # Add GPS data if available
            if latitude and longitude and status != 'absent':
                attendance_data.update({
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'location_accuracy': float(accuracy) if accuracy else 999,
                    'is_location_valid': True,
                })
            
            # Add travel comment if travel not required
            if not travel_required and travel_comment and status != 'absent':
                attendance_data['remarks'] = f'Travel cancelled: {travel_comment}'
            
            # Set travel_approved based on TravelRequest approval status (not user choice)
            if status != 'absent':
                approved_travel_exists = TravelRequest.objects.filter(
                    user=request.user,
                    from_date__lte=today,
                    to_date__gte=today,
                    status='approved'
                ).exists()
                
                # travel_approved reflects Associate's approval, not user's choice
                attendance_data['travel_approved'] = approved_travel_exists
            
            attendance = Attendance.objects.create(**attendance_data)
            
            # Send notification to DC and Admin
            from .notification_service import notify_attendance_marked
            notify_attendance_marked(attendance)
            
            # Create audit log
            create_audit_log(
                request.user,
                'ATTENDANCE_MARKED',
                request,
                f'Status: {status}, Workplace: {workplace}, Travel: {travel_required}'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Check-in successful as {status.replace("_", " ").title()}',
                'check_in_time': current_time.strftime('%I:%M %p') if current_time else None
            })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - always return a response
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    # Check for approved travel requests for today
    has_approved_travel = TravelRequest.objects.filter(
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
        'has_approved_travel': has_approved_travel,
    }
    return render(request, 'authe/mark_attendance_enhanced.html', context)

@login_required
@require_http_methods(["POST"])
def check_out(request):
    """Handle check-out functionality"""
    if request.user.role != 'field_officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Only allow MT, DC, Support designations
    if request.user.designation not in ['MT', 'DC', 'Support']:
        return JsonResponse({'error': 'Check-out is only available for MT, DC, and Support designations.'}, status=403)
    
    today = timezone.localdate()
    
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        
        # Get today's attendance record
        attendance = Attendance.objects.filter(user=request.user, date=today).first()
        
        if not attendance:
            return JsonResponse({'success': False, 'error': 'No check-in record found for today'}, status=400)
        
        if attendance.check_out_time:
            return JsonResponse({'success': False, 'error': 'Already checked out for today'}, status=400)
        
        if attendance.status == 'absent':
            return JsonResponse({'success': False, 'error': 'Cannot check out when marked as absent'}, status=400)
        
        current_time = timezone.localtime().time()
        
        # Update attendance with check-out time
        attendance.check_out_time = current_time
        
        # Add check-out location if available
        if latitude and longitude:
            # Store check-out location in remarks or separate fields if needed
            checkout_location = f'Check-out GPS: {latitude:.6f}, {longitude:.6f}'
            if attendance.remarks:
                attendance.remarks += f' | {checkout_location}'
            else:
                attendance.remarks = checkout_location
        
        attendance.save()
        
        # Create audit log
        create_audit_log(
            request.user,
            'ATTENDANCE_CHECKOUT',
            request,
            f'Check-out at {current_time.strftime("%I:%M %p")}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Check-out successful',
            'check_out_time': current_time.strftime('%I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
            # Handle form data instead of JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
                
            leave_type = data.get('leave_type')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            reason = data.get('reason', '')
            duration = data.get('duration', 'full_day')
            
            # Validate dates
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format')
                return redirect('apply_leave')
            
            if start_date > end_date:
                messages.error(request, 'Start date cannot be after end date')
                return redirect('apply_leave')
            
            # Calculate days requested
            days_diff = (end_date - start_date).days + 1
            if duration == 'half_day' and days_diff == 1:
                days_diff = 0.5
            
            # Create leave request
            leave_request = LeaveRequest.objects.create(
                user=request.user,
                leave_type=leave_type,
                duration=duration,
                start_date=start_date,
                end_date=end_date,
                days_requested=days_diff,
                reason=reason,
                status='pending'
            )
            
            # Create audit log
            create_audit_log(
                request.user,
                'LEAVE_APPLIED',
                request,
                f'Type: {leave_type}, Dates: {start_date} to {end_date}, Reason: {reason}'
            )
            
            # Send notification to admins
            from .notification_service import notify_leave_request
            notify_leave_request(leave_request)
            
            messages.success(request, 'Leave application submitted successfully')
            return redirect('field_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting leave application: {str(e)}')
            return redirect('apply_leave')
    
    # GET request - return leave application form
    recent_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-applied_at')[:5]
    
    context = {
        'user': request.user,
        'leave_types': LeaveRequest.LEAVE_TYPES,
        'leave_requests': recent_leaves,
    }
    return render(request, 'authe/apply_leave.html', context)

@login_required
@require_http_methods(["POST"])
def confirm_team_attendance(request):
    """DC confirmation of team attendance with MANDATORY travel request validation"""
    if request.user.role != 'field_officer' or request.user.designation != 'DC':
        return JsonResponse({'error': 'Access denied. DC privileges required.'}, status=403)
    
    try:
        from .travel_approval_validator import validate_travel_approval_for_dc_confirmation, log_blocked_dc_confirmation
        
        # FORCE DEPLOYMENT: Enhanced validation with debug logging
        def enhanced_validate_with_logging(attendance):
            """Enhanced validation with production logging"""
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"🔍 DC CONFIRMATION CHECK: {attendance.user.employee_id} on {attendance.date}")
            
            # Use original validation
            can_confirm, error_message = validate_travel_approval_for_dc_confirmation(attendance)
            
            if not can_confirm:
                logger.warning(f"🚫 BLOCKED: {attendance.user.employee_id} - {error_message}")
            else:
                logger.info(f"✅ ALLOWED: {attendance.user.employee_id} - DC can confirm")
            
            return can_confirm, error_message
        
        data = json.loads(request.body)
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get team members (ONLY MT and Support)
        team_members = CustomUser.objects.filter(
            role='field_officer',
            dccb=request.user.dccb,
            designation__in=['MT', 'Support']
        ).exclude(id=request.user.id)
        
        confirmed_count = 0
        blocked_records = []
        
        # Process each team member's attendance
        for member in team_members:
            current_date = start_date
            while current_date <= end_date:
                # Get or skip attendance record
                attendance = Attendance.objects.filter(
                    user=member,
                    date=current_date
                ).first()
                
                # Skip if no attendance record exists
                if not attendance:
                    current_date += timedelta(days=1)
                    continue
                
                # Skip if already confirmed
                if attendance.is_confirmed_by_dc:
                    current_date += timedelta(days=1)
                    continue
                
                # MANDATORY VALIDATION: Check travel approval status with enhanced logging
                can_confirm, error_message = enhanced_validate_with_logging(attendance)
                
                if not can_confirm:
                    # BLOCK DC CONFIRMATION
                    blocked_records.append({
                        'employee_id': member.employee_id,
                        'date': current_date.isoformat(),
                        'reason': error_message
                    })
                    
                    # Log blocked attempt
                    log_blocked_dc_confirmation(request.user, attendance, error_message)
                    
                    current_date += timedelta(days=1)
                    continue
                
                # ALLOWED: Confirm attendance
                attendance.is_confirmed_by_dc = True
                attendance.confirmed_by_dc = request.user
                attendance.dc_confirmed_at = timezone.now()
                attendance.confirmation_source = 'DC'
                attendance.save()
                
                confirmed_count += 1
                current_date += timedelta(days=1)
        
        # Create audit log
        AttendanceAuditLog.objects.create(
            action_type='DC_CONFIRMATION',
            dc_user=request.user,
            affected_employee_count=team_members.count(),
            date_range_start=start_date,
            date_range_end=end_date,
            ip_address=request.META.get('REMOTE_ADDR'),
            details=f'Confirmed: {confirmed_count} records. Blocked: {len(blocked_records)} records due to travel approval dependency.'
        )
        
        # Build response message
        if confirmed_count > 0 and len(blocked_records) == 0:
            response_message = f'Successfully confirmed {confirmed_count} attendance records'
        elif confirmed_count > 0 and len(blocked_records) > 0:
            response_message = f'Confirmed {confirmed_count} records. {len(blocked_records)} records blocked due to pending/rejected travel requests'
        elif confirmed_count == 0 and len(blocked_records) > 0:
            response_message = f'No records confirmed. {len(blocked_records)} records blocked due to travel approval requirements'
        else:
            response_message = 'No records to confirm'
        
        return JsonResponse({
            'success': True,
            'message': response_message,
            'confirmed_records': confirmed_count,
            'blocked_records': blocked_records
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)