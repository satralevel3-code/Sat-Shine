from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .notification_service import create_notification
from .models import CustomUser

@login_required
def test_notification_system(request):
    """Test notification system - Admin only"""
    if request.user.role_level < 10:
        return JsonResponse({'success': False, 'error': 'Admin access required'})
    
    if request.method == 'POST':
        # Create test notification for current user
        create_notification(
            recipient=request.user,
            notification_type='system_alert',
            title='Test Notification',
            message=f'This is a test notification sent at {timezone.now().strftime("%H:%M:%S")}',
            priority='medium',
            expires_hours=1
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Test notification created successfully'
        })
    
    return render(request, 'authe/test_notifications.html')

@login_required
def broadcast_notification(request):
    """Broadcast notification to all users - Super Admin only"""
    if request.user.role != 'super_admin':
        return JsonResponse({'success': False, 'error': 'Super Admin access required'})
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        title = data.get('title', 'System Announcement')
        message = data.get('message', 'Test broadcast message')
        priority = data.get('priority', 'medium')
        
        # Send to all active users
        users = CustomUser.objects.filter(is_active=True)
        count = 0
        
        for user in users:
            create_notification(
                recipient=user,
                notification_type='system_alert',
                title=title,
                message=message,
                priority=priority,
                expires_hours=24
            )
            count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Broadcast sent to {count} users'
        })
    
    return JsonResponse({'success': False, 'error': 'POST method required'})