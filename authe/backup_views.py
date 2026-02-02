from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.management import call_command
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, Attendance, TravelRequest, LeaveRequest, Notification
import json
import io
import os
from datetime import datetime

def super_admin_required(view_func):
    """Decorator to ensure only Super Admin can access backup functions"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role_level < 10:
            return JsonResponse({'error': 'Super Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@super_admin_required
def backup_dashboard(request):
    """Backup management dashboard"""
    context = {
        'total_users': CustomUser.objects.count(),
        'total_attendance': Attendance.objects.count(),
        'total_travel': TravelRequest.objects.count(),
        'total_leaves': LeaveRequest.objects.count(),
        'total_notifications': Notification.objects.count(),
    }
    return render(request, 'authe/backup_dashboard.html', context)

@login_required
@super_admin_required
def download_database_backup(request):
    """Download complete database backup as JSON"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create backup data
        backup_data = {
            'backup_info': {
                'timestamp': timestamp,
                'created_by': request.user.employee_id,
                'database_engine': 'SQLite',
                'backup_type': 'complete_web_download'
            },
            'statistics': {
                'total_users': CustomUser.objects.count(),
                'active_users': CustomUser.objects.filter(is_active=True).count(),
                'total_attendance': Attendance.objects.count(),
                'total_travel_requests': TravelRequest.objects.count(),
                'total_leave_requests': LeaveRequest.objects.count(),
                'total_notifications': Notification.objects.count(),
            },
            'data': {
                'users': list(CustomUser.objects.values()),
                'attendance': list(Attendance.objects.values()),
                'travel_requests': list(TravelRequest.objects.values()),
                'leave_requests': list(LeaveRequest.objects.values()),
                'notifications': list(Notification.objects.values()),
            }
        }
        
        # Convert to JSON
        json_data = json.dumps(backup_data, indent=2, default=str)
        
        # Create HTTP response
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="mpmt_backup_{timestamp}.json"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Backup failed: {str(e)}'}, status=500)

@login_required
@super_admin_required
def download_django_backup(request):
    """Download Django dumpdata format backup"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create in-memory file
        output = io.StringIO()
        
        # Run dumpdata command
        call_command('dumpdata', 
                    'authe', 'main',
                    '--indent', '2',
                    '--natural-foreign',
                    stdout=output)
        
        # Get the data
        backup_content = output.getvalue()
        output.close()
        
        # Create HTTP response
        response = HttpResponse(backup_content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="mpmt_django_backup_{timestamp}.json"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Django backup failed: {str(e)}'}, status=500)

@csrf_exempt
@login_required
@super_admin_required
def backup_statistics_api(request):
    """Get current database statistics for backup dashboard"""
    try:
        stats = {
            'users': {
                'total': CustomUser.objects.count(),
                'active': CustomUser.objects.filter(is_active=True).count(),
                'admins': CustomUser.objects.filter(role_level__gte=10).count(),
                'field_officers': CustomUser.objects.filter(role_level__lt=10).count(),
            },
            'attendance': {
                'total': Attendance.objects.count(),
                'today': Attendance.objects.filter(date=timezone.now().date()).count(),
                'this_month': Attendance.objects.filter(
                    date__year=timezone.now().year,
                    date__month=timezone.now().month
                ).count(),
            },
            'travel': {
                'total': TravelRequest.objects.count(),
                'pending': TravelRequest.objects.filter(status='pending').count(),
                'approved': TravelRequest.objects.filter(status='approved').count(),
            },
            'leaves': {
                'total': LeaveRequest.objects.count(),
                'pending': LeaveRequest.objects.filter(status='pending').count(),
                'approved': LeaveRequest.objects.filter(status='approved').count(),
            },
            'notifications': {
                'total': Notification.objects.count(),
                'unread': Notification.objects.filter(is_read=False).count(),
            }
        }
        
        return JsonResponse({'success': True, 'statistics': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@super_admin_required
def emergency_backup_now(request):
    """Emergency backup - creates immediate backup"""
    if request.method == 'POST':
        try:
            # Run the backup script
            import subprocess
            result = subprocess.run(['python', 'create_backup.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return JsonResponse({
                    'success': True, 
                    'message': 'Emergency backup created successfully',
                    'output': result.stdout
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': result.stderr
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST method required'})