from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.db import transaction
from .models import CustomUser, Attendance, TravelRequest, LeaveRequest
from .notification_service import create_notification
import json
from datetime import datetime, date

def super_admin_required(view_func):
    """Decorator to ensure only Super Admin (role_level >= 10) can access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role_level < 10:
            messages.error(request, 'Super Admin access required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@super_admin_required
def enhanced_super_admin_dashboard(request):
    """Enhanced Super Admin Dashboard with all management tools"""
    context = {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'pending_approvals': Attendance.objects.filter(admin_approved=False, dc_confirmed=True).count(),
        'pending_travel': TravelRequest.objects.filter(status='pending').count(),
        'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
    }
    return render(request, 'authe/enhanced_super_admin_dashboard.html', context)

@login_required
@super_admin_required
def password_reset_management(request):
    """Password Reset Management Interface"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        new_password = request.POST.get('new_password')
        
        try:
            user = CustomUser.objects.get(employee_id=employee_id)
            user.set_password(new_password)
            user.save()
            
            # Create notification
            create_notification(
                recipient=user,
                notification_type='system',
                title='Password Reset',
                message=f'Your password has been reset by Super Admin.',
                priority='high'
            )
            
            messages.success(request, f'Password reset successfully for {employee_id}')
        except CustomUser.DoesNotExist:
            messages.error(request, f'Employee {employee_id} not found')
    
    users = CustomUser.objects.all().order_by('employee_id')
    return render(request, 'authe/password_reset_management.html', {'users': users})

@login_required
@super_admin_required
def attendance_marking_interface(request):
    """Attendance Marking Interface for Other Employees"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        attendance_date = request.POST.get('attendance_date')
        status = request.POST.get('status')
        check_in_time = request.POST.get('check_in_time')
        check_out_time = request.POST.get('check_out_time')
        
        try:
            user = CustomUser.objects.get(employee_id=employee_id)
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            
            # Create or update attendance
            attendance, created = Attendance.objects.get_or_create(
                user=user,
                date=attendance_date,
                defaults={
                    'status': status,
                    'check_in_time': check_in_time if check_in_time else None,
                    'check_out_time': check_out_time if check_out_time else None,
                    'dc_confirmed': True,
                    'admin_approved': True,
                    'marked_by_admin': True,
                    'admin_remarks': f'Marked by Super Admin: {request.user.employee_id}'
                }
            )
            
            if not created:
                attendance.status = status
                attendance.check_in_time = check_in_time if check_in_time else attendance.check_in_time
                attendance.check_out_time = check_out_time if check_out_time else attendance.check_out_time
                attendance.dc_confirmed = True
                attendance.admin_approved = True
                attendance.marked_by_admin = True
                attendance.admin_remarks = f'Updated by Super Admin: {request.user.employee_id}'
                attendance.save()
            
            # Create notification
            create_notification(
                recipient=user,
                notification_type='attendance',
                title='Attendance Marked',
                message=f'Your attendance for {attendance_date} has been marked as {status} by Super Admin.',
                priority='medium'
            )
            
            messages.success(request, f'Attendance marked for {employee_id} on {attendance_date}')
        except CustomUser.DoesNotExist:
            messages.error(request, f'Employee {employee_id} not found')
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
    
    users = CustomUser.objects.filter(role_level__lt=10).order_by('employee_id')
    return render(request, 'authe/attendance_marking_interface.html', {'users': users})

@login_required
@super_admin_required
def status_reversal_management(request):
    """Status Reversal Management Interface"""
    attendance_records = Attendance.objects.filter(
        date__gte=timezone.now().date() - timezone.timedelta(days=30)
    ).order_by('-date')
    
    travel_requests = TravelRequest.objects.all().order_by('-created_at')[:50]
    leave_requests = LeaveRequest.objects.all().order_by('-created_at')[:50]
    
    context = {
        'attendance_records': attendance_records,
        'travel_requests': travel_requests,
        'leave_requests': leave_requests,
    }
    return render(request, 'authe/status_reversal_management.html', context)

@csrf_exempt
@login_required
@super_admin_required
def reverse_attendance_status(request):
    """Reverse attendance approval/confirmation status"""
    if request.method == 'POST':
        data = json.loads(request.body)
        attendance_id = data.get('attendance_id')
        action = data.get('action')  # 'toggle_dc' or 'toggle_admin'
        
        try:
            attendance = Attendance.objects.get(id=attendance_id)
            
            if action == 'toggle_dc':
                attendance.dc_confirmed = not attendance.dc_confirmed
                status_text = 'confirmed' if attendance.dc_confirmed else 'unconfirmed'
                message = f'DC status changed to {status_text}'
            elif action == 'toggle_admin':
                attendance.admin_approved = not attendance.admin_approved
                status_text = 'approved' if attendance.admin_approved else 'rejected'
                message = f'Admin status changed to {status_text}'
            
            attendance.admin_remarks = f'Status reversed by Super Admin: {request.user.employee_id}'
            attendance.save()
            
            # Create notification
            create_notification(
                recipient=attendance.user,
                notification_type='attendance',
                title='Attendance Status Changed',
                message=f'Your attendance status for {attendance.date} has been updated by Super Admin.',
                priority='medium'
            )
            
            return JsonResponse({'success': True, 'message': message})
        except Attendance.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Attendance record not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@super_admin_required
def reverse_travel_status(request):
    """Reverse travel request status"""
    if request.method == 'POST':
        data = json.loads(request.body)
        travel_id = data.get('travel_id')
        new_status = data.get('new_status')  # 'pending', 'approved', 'rejected'
        
        try:
            travel_request = TravelRequest.objects.get(id=travel_id)
            old_status = travel_request.status
            travel_request.status = new_status
            travel_request.approved_by = request.user if new_status == 'approved' else None
            travel_request.approved_at = timezone.now() if new_status == 'approved' else None
            travel_request.save()
            
            # Create notification
            create_notification(
                recipient=travel_request.user,
                notification_type='travel',
                title='Travel Request Status Changed',
                message=f'Your travel request status changed from {old_status} to {new_status} by Super Admin.',
                priority='high'
            )
            
            return JsonResponse({'success': True, 'message': f'Travel status changed to {new_status}'})
        except TravelRequest.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Travel request not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@super_admin_required
def bulk_status_operations(request):
    """Bulk status change operations"""
    if request.method == 'POST':
        data = json.loads(request.body)
        operation = data.get('operation')
        record_ids = data.get('record_ids', [])
        
        try:
            with transaction.atomic():
                if operation == 'bulk_approve_attendance':
                    attendances = Attendance.objects.filter(id__in=record_ids)
                    count = attendances.update(
                        admin_approved=True,
                        dc_confirmed=True,
                        admin_remarks=f'Bulk approved by Super Admin: {request.user.employee_id}'
                    )
                    
                    # Create notifications
                    for attendance in attendances:
                        create_notification(
                            recipient=attendance.user,
                            notification_type='attendance',
                            title='Attendance Bulk Approved',
                            message=f'Your attendance for {attendance.date} has been bulk approved.',
                            priority='medium'
                        )
                    
                    return JsonResponse({'success': True, 'message': f'{count} attendance records approved'})
                
                elif operation == 'bulk_reject_attendance':
                    attendances = Attendance.objects.filter(id__in=record_ids)
                    count = attendances.update(
                        admin_approved=False,
                        dc_confirmed=False,
                        admin_remarks=f'Bulk rejected by Super Admin: {request.user.employee_id}'
                    )
                    return JsonResponse({'success': True, 'message': f'{count} attendance records rejected'})
                
                elif operation == 'bulk_approve_travel':
                    travels = TravelRequest.objects.filter(id__in=record_ids)
                    count = travels.update(
                        status='approved',
                        approved_by=request.user,
                        approved_at=timezone.now()
                    )
                    return JsonResponse({'success': True, 'message': f'{count} travel requests approved'})
                
                elif operation == 'bulk_reject_travel':
                    travels = TravelRequest.objects.filter(id__in=record_ids)
                    count = travels.update(status='rejected')
                    return JsonResponse({'success': True, 'message': f'{count} travel requests rejected'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@super_admin_required
def system_override_tools(request):
    """System Override Tools for Emergency Operations"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'reset_all_passwords':
            # Emergency password reset for all users
            users = CustomUser.objects.all()
            for user in users:
                user.set_password('reset123')
                user.save()
            messages.success(request, 'All passwords reset to "reset123"')
        
        elif action == 'approve_all_pending':
            # Approve all pending items
            Attendance.objects.filter(admin_approved=False).update(
                admin_approved=True,
                dc_confirmed=True,
                admin_remarks=f'Emergency approval by Super Admin: {request.user.employee_id}'
            )
            TravelRequest.objects.filter(status='pending').update(
                status='approved',
                approved_by=request.user,
                approved_at=timezone.now()
            )
            LeaveRequest.objects.filter(status='pending').update(
                status='approved',
                approved_by=request.user,
                approved_at=timezone.now()
            )
            messages.success(request, 'All pending items approved')
    
    return render(request, 'authe/system_override_tools.html')