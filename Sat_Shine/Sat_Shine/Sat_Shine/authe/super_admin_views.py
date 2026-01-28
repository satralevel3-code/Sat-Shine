# Super Admin Dashboard - Full System Control

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from .models import CustomUser, Attendance, LeaveRequest, TravelRequest, SystemAuditLog
import csv
import json

@login_required
def super_admin_dashboard(request):
    """Super Admin dashboard with full system control"""
    if request.user.role != 'super_admin':
        messages.error(request, 'Super Admin privileges required')
        return redirect('field_dashboard')
    
    today = timezone.localdate()
    
    # Daily attendance progress calculation
    total_employees = CustomUser.objects.filter(is_active=True, role='field_officer').count()
    marked_today = Attendance.objects.filter(date=today).count()
    progress_percentage = (marked_today / total_employees * 100) if total_employees > 0 else 0
    
    # System KPIs
    kpis = {
        'total_users': CustomUser.objects.filter(is_active=True).count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'inactive_users': CustomUser.objects.filter(is_active=False).count(),
        'attendance_anomalies': Attendance.objects.filter(
            date=today, 
            check_in_time__gt=time(14, 30)
        ).count(),
        'approval_backlogs': Attendance.objects.filter(
            is_confirmed_by_dc=True,
            is_approved_by_admin=False
        ).count(),
        'daily_progress': progress_percentage,
        'marked_today': marked_today,
        'pending_today': total_employees - marked_today
    }
    
    # Recent system activities
    recent_activities = SystemAuditLog.objects.select_related('actor').order_by('-timestamp')[:15]
    
    context = {
        'user': request.user,
        'kpis': kpis,
        'recent_activities': recent_activities,
        'today': today,
        'current_time': timezone.now()
    }
    
    return render(request, 'authe/super_admin_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Enhanced Admin dashboard with comprehensive KPIs"""
    if request.user.role_level < 10:
        messages.error(request, 'Admin privileges required')
        return redirect('field_dashboard')
    
    today = timezone.localdate()
    
    # Enhanced KPI calculations
    total_employees = CustomUser.objects.filter(is_active=True, role='field_officer').count()
    today_attendance = Attendance.objects.filter(date=today)
    
    kpis = {
        'total_employees': total_employees,
        'present_today': today_attendance.filter(status='present').count(),
        'absent_today': today_attendance.filter(status='absent').count(),
        'half_day_today': today_attendance.filter(status='half_day').count(),
        'late_arrivals': today_attendance.filter(time_status='late').count(),
        'not_marked': total_employees - today_attendance.count(),
        'dc_confirmations_pending': Attendance.objects.filter(
            date__gte=today - timedelta(days=7),
            is_confirmed_by_dc=False
        ).count(),
        'admin_approvals_pending': Attendance.objects.filter(
            is_confirmed_by_dc=True,
            is_approved_by_admin=False
        ).count(),
        'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
        'pending_travels': TravelRequest.objects.filter(status='pending').count()
    }
    
    context = {
        'user': request.user,
        'kpis': kpis,
        'today': today,
        'current_time': timezone.now()
    }
    
    return render(request, 'authe/admin_dashboard.html', context)

@login_required
def employee_master(request):
    """Employee Master Management Screen"""
    if request.user.role_level < 10:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    
    # Filters
    dccb_filter = request.GET.get('dccb')
    designation_filter = request.GET.get('designation')
    emp_id_filter = request.GET.get('emp_id')
    name_filter = request.GET.get('name')
    status_filter = request.GET.get('status', 'active')
    manager_filter = request.GET.get('manager')
    
    employees = CustomUser.objects.all()
    
    if dccb_filter:
        employees = employees.filter(dccb=dccb_filter)
    if designation_filter:
        employees = employees.filter(designation=designation_filter)
    if emp_id_filter:
        employees = employees.filter(employee_id__icontains=emp_id_filter)
    if name_filter:
        employees = employees.filter(
            Q(first_name__icontains=name_filter) | 
            Q(last_name__icontains=name_filter)
        )
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    if manager_filter:
        employees = employees.filter(reporting_manager__icontains=manager_filter)
    
    employees = employees.order_by('employee_id')
    
    context = {
        'user': request.user,
        'employees': employees,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'designation_choices': CustomUser.DESIGNATION_CHOICES,
        'filters': {
            'dccb': dccb_filter,
            'designation': designation_filter,
            'emp_id': emp_id_filter,
            'name': name_filter,
            'status': status_filter,
            'manager': manager_filter
        }
    }
    
    return render(request, 'authe/employee_master.html', context)

@login_required
def todays_attendance_details(request):
    """Today's Attendance Details Screen"""
    if request.user.role_level < 10:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    
    today = timezone.localdate()
    attendance_records = Attendance.objects.filter(date=today).select_related('user').order_by('user__employee_id')
    
    context = {
        'user': request.user,
        'attendance_records': attendance_records,
        'today': today
    }
    
    return render(request, 'authe/todays_attendance_details.html', context)

@login_required
def dc_confirmation_screen(request):
    """DC Confirmation Monitoring Screen"""
    if request.user.role_level < 10:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    dccb_filter = request.GET.get('dccb')
    emp_id_filter = request.GET.get('emp_id')
    
    # Default to last 7 days
    if not start_date:
        start_date = (timezone.localdate() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.localdate().strftime('%Y-%m-%d')
    
    attendance_records = Attendance.objects.filter(
        date__range=[start_date, end_date],
        is_confirmed_by_dc=False
    ).select_related('user')
    
    if dccb_filter:
        attendance_records = attendance_records.filter(user__dccb=dccb_filter)
    if emp_id_filter:
        attendance_records = attendance_records.filter(user__employee_id__icontains=emp_id_filter)
    
    context = {
        'user': request.user,
        'attendance_records': attendance_records,
        'start_date': start_date,
        'end_date': end_date,
        'dccb_choices': CustomUser.DCCB_CHOICES,
        'filters': {
            'dccb': dccb_filter,
            'emp_id': emp_id_filter
        }
    }
    
    return render(request, 'authe/dc_confirmation_screen.html', context)

@login_required
@csrf_exempt
def bulk_attendance_approval(request):
    """Bulk Attendance Approval for Payroll"""
    if not request.user.can_approve_attendance:
        return JsonResponse({'error': 'Attendance approval permission required'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
            
            # Get DC confirmed records only (payroll cycle 25th to 25th)
            attendance_records = Attendance.objects.filter(
                date__range=[start_date, end_date],
                is_confirmed_by_dc=True,
                is_approved_by_admin=False
            )
            
            approved_count = 0
            for attendance in attendance_records:
                # Apply payroll rules: NM → Absent, P → Present, H → Half Day
                if attendance.status == 'auto_not_marked':
                    attendance.status = 'absent'
                
                attendance.is_approved_by_admin = True
                attendance.approved_by_admin = request.user
                attendance.admin_approved_at = timezone.now()
                attendance.save()
                approved_count += 1
            
            return JsonResponse({
                'success': True,
                'approved_count': approved_count,
                'message': f'Approved {approved_count} attendance records for payroll'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST method required'}, status=405)