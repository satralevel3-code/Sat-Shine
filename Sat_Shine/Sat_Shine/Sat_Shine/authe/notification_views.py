from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Notification
import json

@login_required
def get_notifications(request):
    """Get notifications for current user (excluding expired)"""
    # Clean up expired notifications first
    from .notification_service import cleanup_expired_notifications
    cleanup_expired_notifications()
    
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:15]
    
    notification_data = []
    for notif in notifications:
        if not notif.is_expired:  # Skip expired notifications
            notification_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type,
                'priority': notif.priority,
                'is_read': notif.is_read,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': get_time_ago(notif.created_at)
            })
    
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).exclude(expires_at__lt=timezone.now()).count()
    
    return JsonResponse({
        'notifications': notification_data,
        'unread_count': unread_count
    })

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return JsonResponse({'success': True})

def get_time_ago(timestamp):
    """Get human readable time ago"""
    now = timezone.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"