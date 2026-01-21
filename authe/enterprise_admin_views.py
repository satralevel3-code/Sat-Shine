# Enterprise Admin Dashboard for MMP

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from .models import CustomUser, Attendance, LeaveRequest, TravelRequest, SystemAuditLog
from .enterprise_permissions import check_hierarchy_permission, log_enterprise_action
import csv
import json

@login_required
def enterprise_dashboard(request):
    """Enterprise admin dashboard with KPIs"""
    if request.user.role_level < 10:  # Admin level and above
        messages.error(request, 'Admin privileges required')
        return redirect('field_dashboard')
    
    today = timezone.localdate()
    
    # KPI Calculations
    total_employees = CustomUser.objects.filter(is_active=True).count()
    today_attendance = Attendance.objects.filter(date=today)
    
    kpis = {
        'total_employees': total_employees,
        'present_today': today_attendance.filter(status='present').count(),
        'absent_today': today_attendance.filter(status='absent').count(),
        'half_day_today': today_attendance.filter(status='half_day').count(),
        'not_marked': total_employees - today_attendance.count(),
        'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
        'pending_travels': TravelRequest.objects.filter(status='pending').count(),
        'dc_confirmations_pending': Attendance.objects.filter(
            date__gte=today - timedelta(days=7),
            is_confirmed_by_dc=False
        ).count()
    }
    
    # Recent activities
    recent_activities = SystemAuditLog.objects.select_related('actor').order_by('-timestamp')[:10]
    
    # DCCB-wise summary
    dccb_summary = CustomUser.objects.filter(is_active=True).values('dccb').annotate(
        total=Count('id'),
        present=Count('attendance', filter=Q(attendance__date=today, attendance__status='present')),
        absent=Count('attendance', filter=Q(attendance__date=today, attendance__status='absent'))
    ).order_by('dccb')
    
    context = {
        'user': request.user,
        'kpis': kpis,
        'recent_activities': recent_activities,
        'dccb_summary': dccb_summary,
        'today': today
    }
    
    return render(request, 'authe/enterprise_dashboard.html', context)

@login_required
def employee_management(request):
    """Enterprise employee management"""
    if request.user.role_level < 10:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    
    employees = CustomUser.objects.filter(is_active=True).order_by('employee_id')
    
    context = {
        'user': request.user,
        'employees': employees,
    }
    
    return render(request, 'authe/employee_management.html', context)