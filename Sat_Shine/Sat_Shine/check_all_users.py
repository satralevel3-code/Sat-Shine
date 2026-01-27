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

print("=== All Users Check ===")

# Check all users
all_users = CustomUser.objects.all()
print(f"Total users: {all_users.count()}")

for user in all_users:
    print(f"  {user.employee_id} - {user.first_name} {user.last_name} - {user.designation} - {user.dccb}")

print("\n=== Attendance Records for Jan 9, 2025 ===")
check_date = date(2025, 1, 9)
attendance_records = Attendance.objects.filter(date=check_date)

for record in attendance_records:
    print(f"  {record.user.employee_id}: Status={record.status}, DC_Confirmed={record.is_confirmed_by_dc}")