#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from datetime import date

print("=== Admin Dashboard Test ===")

# Test the admin dashboard logic for January 9, 2026
test_date = date(2026, 1, 9)
print(f"Testing for date: {test_date}")

# Get employees
employees = CustomUser.objects.filter(role='field_officer', is_active=True)
print(f"Active employees: {employees.count()}")

# Get attendance records for the test date
attendance_records = Attendance.objects.filter(date=test_date).select_related('user')
print(f"Attendance records for {test_date}: {attendance_records.count()}")

# Organize attendance by employee and date (same logic as admin_views.py)
attendance_dict = {}
for record in attendance_records:
    if record.user.employee_id not in attendance_dict:
        attendance_dict[record.user.employee_id] = {}
    
    # Determine final status considering DC confirmation
    final_status = record.status
    if record.is_confirmed_by_dc and record.status == 'auto_not_marked':
        final_status = 'absent'  # DC confirmed NM records become Absent
    
    attendance_dict[record.user.employee_id][record.date] = {
        'status': final_status,
        'is_dc_confirmed': record.is_confirmed_by_dc
    }

print(f"\\nAttendance Dictionary:")
for emp_id, dates in attendance_dict.items():
    for date_obj, data in dates.items():
        print(f"  {emp_id} - {date_obj}: Status={data['status']}, DC_Confirmed={data['is_dc_confirmed']}")

# Test what the admin dashboard would show
print(f"\\nAdmin Dashboard Display:")
for employee in employees:
    attendance = attendance_dict.get(employee.employee_id, {}).get(test_date, {})
    status = attendance.get('status', 'not_marked')
    
    # Check if this employee has DC confirmed attendance for dates not in records
    if status == 'not_marked':
        # Check if there's a DC confirmed record that would make this absent
        dc_confirmed_record = Attendance.objects.filter(
            user=employee,
            date=test_date,
            is_confirmed_by_dc=True
        ).first()
        
        if dc_confirmed_record:
            status = 'absent'  # DC confirmed NM becomes Absent
    
    display_status = 'P' if status == 'present' else 'A' if status == 'absent' else 'H' if status == 'half_day' else 'NM'
    dc_confirmed = attendance.get('is_dc_confirmed', False)
    
    print(f"  {employee.employee_id}: Display={display_status}, DC_Confirmed={dc_confirmed}")