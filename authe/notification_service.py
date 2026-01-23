from django.utils import timezone
from datetime import timedelta
from .models import Notification, CustomUser

def create_notification(recipient, notification_type, title, message, priority='medium', expires_hours=4, related_object_id=None):
    """Create a new notification with auto-expiry"""
    expires_at = timezone.now() + timedelta(hours=expires_hours)
    
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        expires_at=expires_at,
        related_object_id=related_object_id
    )

def clear_related_notifications(related_object_id, notification_type=None):
    """Clear notifications related to a specific object/action"""
    query = Notification.objects.filter(related_object_id=related_object_id)
    if notification_type:
        query = query.filter(notification_type=notification_type)
    
    query.delete()

def cleanup_expired_notifications():
    """Remove expired notifications"""
    expired_count = Notification.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]
    return expired_count

def send_check_in_reminder():
    """Send check-in reminder to all active field officers"""
    field_officers = CustomUser.objects.filter(
        role='field_officer',
        is_active=True,
        designation__in=['MT', 'DC', 'Support']
    )
    
    for officer in field_officers:
        create_notification(
            recipient=officer,
            notification_type='check_in_reminder',
            title='Check-in Reminder',
            message='Please check in on time. Remember to mark your attendance before 9:30 AM.',
            priority='medium'
        )

def notify_travel_request(travel_request):
    """Notify Associate about new travel request"""
    if travel_request.request_to:
        create_notification(
            recipient=travel_request.request_to,
            notification_type='travel_request',
            title='New Travel Request',
            message=f'Travel request from {travel_request.user.employee_id} for {travel_request.from_date} requires your approval.',
            priority='high',
            related_object_id=f'travel_{travel_request.id}'
        )

def notify_travel_approval(travel_request, approved=True):
    """Notify user about travel request approval/rejection"""
    # Clear the pending travel request notification
    clear_related_notifications(f'travel_{travel_request.id}', 'travel_request')
    
    status = 'approved' if approved else 'rejected'
    create_notification(
        recipient=travel_request.user,
        notification_type='travel_approval',
        title=f'Travel Request {status.title()}',
        message=f'Your travel request for {travel_request.from_date} has been {status}.',
        priority='high',
        expires_hours=2  # Shorter expiry for approval notifications
    )

def notify_leave_request(leave_request):
    """Notify admin about new leave request"""
    admins = CustomUser.objects.filter(role_level__gte=10, is_active=True)
    for admin in admins:
        create_notification(
            recipient=admin,
            notification_type='leave_request',
            title='New Leave Request',
            message=f'Leave request from {leave_request.user.employee_id} for {leave_request.start_date} requires approval.',
            priority='medium',
            related_object_id=f'leave_{leave_request.id}'
        )

def notify_leave_approval(leave_request, approved=True):
    """Notify user about leave approval/rejection"""
    # Clear the pending leave request notifications
    clear_related_notifications(f'leave_{leave_request.id}', 'leave_request')
    
    status = 'approved' if approved else 'rejected'
    create_notification(
        recipient=leave_request.user,
        notification_type='leave_approval',
        title=f'Leave Request {status.title()}',
        message=f'Your leave request for {leave_request.start_date} has been {status}.',
        priority='high',
        expires_hours=2
    )

def notify_attendance_marked(attendance):
    """Notify DC and Admin when user marks attendance"""
    # Notify DC of same DCCB
    dcs = CustomUser.objects.filter(
        designation='DC',
        dccb=attendance.user.dccb,
        is_active=True
    )
    
    for dc in dcs:
        create_notification(
            recipient=dc,
            notification_type='system_alert',
            title='Attendance Marked',
            message=f'{attendance.user.employee_id} marked attendance as {attendance.status} at {attendance.check_in_time or "N/A"}',
            priority='low'
        )
    
    # Notify Admins
    admins = CustomUser.objects.filter(role_level__gte=10, is_active=True)
    for admin in admins:
        create_notification(
            recipient=admin,
            notification_type='system_alert',
            title='Daily Attendance Update',
            message=f'{attendance.user.employee_id} ({attendance.user.dccb}) marked {attendance.status}',
            priority='low'
        )

def notify_dc_confirmation(dc_user, confirmed_count, date_range):
    """Notify Admin when DC confirms attendance"""
    admins = CustomUser.objects.filter(role_level__gte=10, is_active=True)
    for admin in admins:
        create_notification(
            recipient=admin,
            notification_type='system_alert',
            title='DC Confirmation Completed',
            message=f'DC {dc_user.employee_id} confirmed {confirmed_count} attendance records for {date_range}',
            priority='medium'
        )

def notify_dc_confirmation_to_user(user, dc_user):
    """Notify MT/Support when their attendance is confirmed by DC"""
    if user.designation in ['MT', 'Support']:
        create_notification(
            recipient=user,
            notification_type='system_alert',
            title='Attendance Confirmed by DC',
            message=f'Your attendance has been confirmed by DC {dc_user.employee_id}',
            priority='medium'
        )

def notify_admin_approval_to_user(user, admin_user):
    """Notify MT/Support when their attendance is approved by Admin"""
    if user.designation in ['MT', 'Support']:
        create_notification(
            recipient=user,
            notification_type='system_alert',
            title='Attendance Approved by Admin',
            message=f'Your attendance has been approved by Admin {admin_user.employee_id}',
            priority='medium'
        )