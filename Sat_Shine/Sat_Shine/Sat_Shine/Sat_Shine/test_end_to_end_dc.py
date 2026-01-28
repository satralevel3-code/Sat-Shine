#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from datetime import date, timedelta
from django.utils import timezone

print("=== END-TO-END DC CONFIRMATION TEST ===")

# Get today's date
today = timezone.localdate()
print(f"Testing for date: {today}")

# Get users
dc_user = CustomUser.objects.filter(designation='DC').first()
mt_user = CustomUser.objects.filter(designation='MT').first()

print(f"DC User: {dc_user.employee_id}")
print(f"MT User: {mt_user.employee_id}")

# Step 1: Clear any existing attendance for today
Attendance.objects.filter(user=mt_user, date=today).delete()
print(f"Cleared existing attendance for {mt_user.employee_id}")

# Step 2: Verify MT user has no attendance (should see "Not Marked")
mt_attendance = Attendance.objects.filter(user=mt_user, date=today).first()
print(f"MT User attendance before DC confirmation: {mt_attendance}")

# Step 3: DC confirms attendance (creates absent record)
attendance, created = Attendance.objects.get_or_create(
    user=mt_user,
    date=today,
    defaults={
        'status': 'absent',
        'is_confirmed_by_dc': True,
        'confirmed_by_dc': dc_user,
        'dc_confirmed_at': timezone.now(),
        'confirmation_source': 'DC'
    }
)

print(f"DC confirmation created: {created}")
print(f"Attendance record: {attendance.status}, DC Confirmed: {attendance.is_confirmed_by_dc}")

# Step 4: Test what MT user sees in dashboard
mt_attendance_after = Attendance.objects.filter(user=mt_user, date=today).first()
print(f"MT User attendance after DC confirmation: {mt_attendance_after}")

if mt_attendance_after:
    print(f"Status: {mt_attendance_after.status}")
    print(f"DC Confirmed: {mt_attendance_after.is_confirmed_by_dc}")
    print(f"Confirmed by: {mt_attendance_after.confirmed_by_dc.employee_id if mt_attendance_after.confirmed_by_dc else 'None'}")
    
    # What MT user should see in dashboard
    if mt_attendance_after.status == 'absent' and mt_attendance_after.is_confirmed_by_dc:
        dashboard_display = f"Absent (DC Confirmed by {mt_attendance_after.confirmed_by_dc.employee_id})"
    else:
        dashboard_display = mt_attendance_after.get_status_display()
    
    print(f"Dashboard Display: {dashboard_display}")

# Step 5: Test admin dashboard display
print(f"\nAdmin Dashboard Test:")
print(f"Employee: {mt_user.employee_id}")
print(f"Status: {mt_attendance_after.status if mt_attendance_after else 'not_marked'}")
print(f"Display: {'A' if mt_attendance_after and mt_attendance_after.status == 'absent' else 'NM'}")

print(f"\n=== TEST COMPLETE ===")
print(f"Expected Results:")
print(f"1. MT User Dashboard: Shows 'Absent (DC Confirmed by {dc_user.employee_id})'")
print(f"2. Admin Dashboard: Shows 'A' badge for {mt_user.employee_id}")
print(f"3. Attendance History: Shows absent with DC confirmation indicator")