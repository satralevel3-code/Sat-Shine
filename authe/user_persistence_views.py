from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import CustomUser
from .admin_views import admin_required
import json
import os

@login_required
@admin_required
def verify_user_persistence(request):
    """Verify user data persistence and backup system"""
    
    if request.method == 'POST':
        # Manual backup trigger
        try:
            import subprocess
            result = subprocess.run(['python', 'backup_users.py'], 
                                  capture_output=True, text=True, cwd='/app')
            
            return JsonResponse({
                'success': True,
                'message': 'Manual backup completed',
                'output': result.stdout
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # Get current user statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    admin_users = CustomUser.objects.filter(role_level__gte=10).count()
    field_officers = CustomUser.objects.filter(role='field_officer').count()
    
    # Check backup file status
    backup_exists = os.path.exists('/app/user_backup.json')
    backup_size = 0
    backup_users_count = 0
    
    if backup_exists:
        try:
            backup_size = os.path.getsize('/app/user_backup.json')
            with open('/app/user_backup.json', 'r') as f:
                backup_data = json.load(f)
                backup_users_count = len(backup_data)
        except:
            backup_exists = False
    
    # Get recent users (created in last 7 days)
    week_ago = timezone.now() - timezone.timedelta(days=7)
    recent_users = CustomUser.objects.filter(
        date_joined__gte=week_ago
    ).order_by('-date_joined')
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'field_officers': field_officers,
        'backup_exists': backup_exists,
        'backup_size': backup_size,
        'backup_users_count': backup_users_count,
        'recent_users': recent_users,
        'current_time': timezone.now(),
    }
    
    return render(request, 'authe/verify_user_persistence.html', context)

@login_required
@admin_required
def user_persistence_api(request):
    """API endpoint for user persistence data"""
    
    # Get user counts by role
    role_counts = {}
    for role, _ in CustomUser.ROLE_CHOICES:
        role_counts[role] = CustomUser.objects.filter(role=role).count()
    
    # Get designation counts
    designation_counts = {}
    for designation, _ in CustomUser.DESIGNATION_CHOICES:
        designation_counts[designation] = CustomUser.objects.filter(designation=designation).count()
    
    # Get DCCB distribution
    dccb_counts = {}
    for dccb, _ in CustomUser.DCCB_CHOICES:
        dccb_counts[dccb] = CustomUser.objects.filter(dccb=dccb).count()
    
    return JsonResponse({
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'role_distribution': role_counts,
        'designation_distribution': designation_counts,
        'dccb_distribution': dccb_counts,
        'timestamp': timezone.now().isoformat()
    })