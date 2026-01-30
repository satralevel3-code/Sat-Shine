#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, AttendanceAuditLog
from datetime import date

print("=== DC Confirmation Analysis ===")

# Find DC user
dc_user = CustomUser.objects.filter(designation='DC').first()
if dc_user:
    print(f"DC User: {dc_user.employee_id} - {dc_user.first_name} {dc_user.last_name}")
    
    # Check if DC has confirmed any attendance
    audit_logs = AttendanceAuditLog.objects.filter(dc_user=dc_user)
    print(f"DC Audit Logs: {audit_logs.count()}")
    
    for log in audit_logs:
        print(f"  {log.timestamp}: {log.action_type} - {log.details}")
    
    # Check DC confirmed attendance records
    dc_confirmed = Attendance.objects.filter(confirmed_by_dc=dc_user)
    print(f"DC Confirmed Records: {dc_confirmed.count()}")
    
    for record in dc_confirmed:
        print(f"  {record.user.employee_id} - {record.date}: Status={record.status}, DC_Confirmed={record.is_confirmed_by_dc}")

# Check all attendance records
print(f"\n=== All Attendance Records ===")
all_attendance = Attendance.objects.all().order_by('-date')
for record in all_attendance:
    print(f"  {record.user.employee_id} - {record.date}: Status={record.status}, DC_Confirmed={record.is_confirmed_by_dc}")

# Check for any records with auto_not_marked status
auto_nm_records = Attendance.objects.filter(status='auto_not_marked')
print(f"\nAuto Not Marked Records: {auto_nm_records.count()}")
for record in auto_nm_records:
    print(f"  {record.user.employee_id} - {record.date}: DC_Confirmed={record.is_confirmed_by_dc}")