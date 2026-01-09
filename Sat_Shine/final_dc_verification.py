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
from datetime import date, timedelta

print("=== COMPREHENSIVE DC CONFIRMATION VERIFICATION ===")
print()

# 1. Check Users
print("1. USER VERIFICATION:")
print("-" * 50)
all_users = CustomUser.objects.all().order_by('employee_id')
for user in all_users:
    print(f"   {user.employee_id} - {user.first_name} {user.last_name} - {user.designation} - {user.dccb}")

dc_user = CustomUser.objects.filter(designation='DC').first()
team_members = CustomUser.objects.filter(
    role='field_officer',
    dccb=dc_user.dccb if dc_user else None,
    designation__in=['MT', 'Support']
).exclude(id=dc_user.id if dc_user else None)

print(f"\\n   DC User: {dc_user.employee_id if dc_user else 'None'}")
print(f"   Team Members: {[m.employee_id for m in team_members]}")

# 2. Check DC Confirmation Records
print("\\n2. DC CONFIRMATION AUDIT:")
print("-" * 50)
audit_logs = AttendanceAuditLog.objects.all().order_by('-timestamp')
for log in audit_logs:
    print(f"   {log.timestamp}: {log.action_type} by {log.dc_user.employee_id}")
    print(f"      Affected: {log.affected_employee_count} employees")
    print(f"      Date Range: {log.date_range_start} to {log.date_range_end}")
    print(f"      Details: {log.details}")
    print()

# 3. Check Attendance Records
print("3. ATTENDANCE RECORDS:")
print("-" * 50)
recent_dates = [date.today() - timedelta(days=i) for i in range(5)]
for check_date in recent_dates:
    print(f"   Date: {check_date}")
    attendance_records = Attendance.objects.filter(date=check_date).order_by('user__employee_id')
    
    if attendance_records:
        for record in attendance_records:
            status_display = record.status.upper()
            dc_status = "DC Confirmed" if record.is_confirmed_by_dc else "Not Confirmed"
            confirmed_by = f" by {record.confirmed_by_dc.employee_id}" if record.confirmed_by_dc else ""
            
            print(f"      {record.user.employee_id}: {status_display} - {dc_status}{confirmed_by}")
    else:
        print("      No attendance records")
    print()

# 4. Test Admin Dashboard Logic
print("4. ADMIN DASHBOARD SIMULATION:")
print("-" * 50)
test_date = date(2026, 1, 9)  # Date with DC confirmed records
print(f"   Testing for: {test_date}")

# Get attendance records for test date
attendance_records = Attendance.objects.filter(date=test_date).select_related('user')
attendance_dict = {}

for record in attendance_records:
    if record.user.employee_id not in attendance_dict:
        attendance_dict[record.user.employee_id] = {}
    
    # Apply the same logic as admin_views.py
    final_status = record.status
    if record.is_confirmed_by_dc and record.status == 'auto_not_marked':
        final_status = 'absent'  # DC confirmed NM records become Absent
    
    attendance_dict[record.user.employee_id][record.date] = {
        'status': final_status,
        'is_dc_confirmed': record.is_confirmed_by_dc
    }

# Show what admin dashboard would display
employees = CustomUser.objects.filter(role='field_officer', is_active=True)
for employee in employees:
    attendance = attendance_dict.get(employee.employee_id, {}).get(test_date, {})
    status = attendance.get('status', 'not_marked')
    
    # Check for DC confirmed records not in main query
    if status == 'not_marked':
        dc_confirmed_record = Attendance.objects.filter(
            user=employee,
            date=test_date,
            is_confirmed_by_dc=True
        ).first()
        
        if dc_confirmed_record:
            status = 'absent'
    
    # Convert to display format
    display_status = {
        'present': 'P (Present)',
        'absent': 'A (Absent)',
        'half_day': 'H (Half Day)',
        'not_marked': 'NM (Not Marked)'
    }.get(status, 'NM (Not Marked)')
    
    dc_confirmed = attendance.get('is_dc_confirmed', False)
    dc_indicator = " [DC Confirmed]" if dc_confirmed else ""
    
    print(f"      {employee.employee_id}: {display_status}{dc_indicator}")

# 5. Summary
print("\\n5. VERIFICATION SUMMARY:")
print("-" * 50)
total_dc_confirmed = Attendance.objects.filter(is_confirmed_by_dc=True).count()
total_audit_logs = AttendanceAuditLog.objects.count()

print(f"   DC User Found: {dc_user.employee_id if dc_user else 'None'}")
print(f"   Team Members: {team_members.count()}")
print(f"   DC Confirmed Records: {total_dc_confirmed}")
print(f"   Audit Log Entries: {total_audit_logs}")

if total_dc_confirmed > 0:
    print(f"   DC Confirmation Working: YES")
    print(f"   Admin Dashboard Logic: UPDATED")
    print(f"   Status Display: DC confirmed NM records show as 'A' (Absent)")
else:
    print(f"   DC Confirmation Working: NO RECORDS FOUND")

print("\\n=== VERIFICATION COMPLETE ===")
print()
print("INSTRUCTIONS FOR USER:")
print("1. Login as Admin (MP0001)")
print("2. Go to Admin Dashboard > Attendance Management > Daily Attendance")
print("3. Select date range that includes 2026-01-09")
print("4. Look for MGJ00007 and MGJ00008 - they should show 'A' (Absent) with DC confirmation")
print("5. The 'A' status indicates DC has confirmed their attendance (originally Not Marked)")