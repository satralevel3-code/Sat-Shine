#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from datetime import date
from django.utils import timezone

print("=== TEMPLATE LOGIC TEST ===")

# Get MT user and today's attendance
mt_user = CustomUser.objects.filter(designation='MT').first()
today = timezone.localdate()

print(f"MT User: {mt_user.employee_id}")
print(f"Date: {today}")

# Get attendance record
today_attendance = Attendance.objects.filter(user=mt_user, date=today).first()

print(f"\nAttendance Record:")
if today_attendance:
    print(f"  Status: {today_attendance.status}")
    print(f"  DC Confirmed: {today_attendance.is_confirmed_by_dc}")
    print(f"  Confirmed By: {today_attendance.confirmed_by_dc.employee_id if today_attendance.confirmed_by_dc else 'None'}")
    print(f"  Marked At: {today_attendance.marked_at}")
    
    # Template logic test
    print(f"\nTemplate Logic Test:")
    print(f"  today_attendance exists: {today_attendance is not None}")
    print(f"  status == 'absent': {today_attendance.status == 'absent'}")
    print(f"  is_confirmed_by_dc: {today_attendance.is_confirmed_by_dc}")
    
    # What template should render
    if today_attendance.status == 'absent' and today_attendance.is_confirmed_by_dc:
        template_output = f"Absent (DC Confirmed) - Confirmed by {today_attendance.confirmed_by_dc.employee_id}"
        button_state = "Already Marked (disabled)"
    else:
        template_output = f"{today_attendance.get_status_display()} - Marked at {today_attendance.marked_at.strftime('%I:%M %p') if today_attendance.marked_at else 'N/A'}"
        button_state = "Already Marked (disabled)"
    
    print(f"\nTemplate Should Show:")
    print(f"  Badge: {template_output}")
    print(f"  Button: {button_state}")
    
else:
    print("  No attendance record found")
    print(f"\nTemplate Should Show:")
    print(f"  Badge: Not Marked")
    print(f"  Button: Mark Attendance")

print(f"\n=== VERIFICATION STEPS ===")
print(f"1. Login as {mt_user.employee_id}")
print(f"2. Go to field dashboard")
print(f"3. Look for debug info showing attendance details")
print(f"4. Check if status shows as expected above")

# Also check if there are multiple records
all_records = Attendance.objects.filter(user=mt_user, date=today)
print(f"\nAll records for {mt_user.employee_id} on {today}: {all_records.count()}")
for i, record in enumerate(all_records):
    print(f"  Record {i+1}: {record.status}, DC: {record.is_confirmed_by_dc}")