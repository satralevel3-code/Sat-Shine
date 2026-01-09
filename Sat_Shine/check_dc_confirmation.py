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

print("=== DC Confirmation Status Check ===")

# Check DC user
dc_user = CustomUser.objects.filter(employee_id='MGJ00002', designation='DC').first()
if dc_user:
    print(f"DC User: {dc_user.employee_id} - {dc_user.first_name} {dc_user.last_name}")
else:
    print("DC User MGJ00002 not found")
    exit()

# Check team member
team_member = CustomUser.objects.filter(employee_id='MGJ00001').first()
if team_member:
    print(f"Team Member: {team_member.employee_id} - {team_member.first_name} {team_member.last_name}")
else:
    print("Team Member MGJ00001 not found")
    exit()

# Check attendance records for January 9, 2025
check_date = date(2025, 1, 9)
print(f"\nChecking attendance for {check_date}:")

attendance_record = Attendance.objects.filter(
    user=team_member,
    date=check_date
).first()

if attendance_record:
    print(f"Attendance Record Found:")
    print(f"  Status: {attendance_record.status}")
    print(f"  Is DC Confirmed: {attendance_record.is_confirmed_by_dc}")
    print(f"  Confirmed By: {attendance_record.confirmed_by_dc}")
    print(f"  DC Confirmed At: {attendance_record.dc_confirmed_at}")
    print(f"  Check-in Time: {attendance_record.check_in_time}")
else:
    print("No attendance record found for this date")

# Check all DC confirmed records
print(f"\nAll DC confirmed records for {team_member.employee_id}:")
dc_confirmed_records = Attendance.objects.filter(
    user=team_member,
    is_confirmed_by_dc=True
).order_by('-date')

for record in dc_confirmed_records:
    print(f"  {record.date}: Status={record.status}, Confirmed by {record.confirmed_by_dc.employee_id if record.confirmed_by_dc else 'None'}")

print(f"\nTotal DC confirmed records: {dc_confirmed_records.count()}")