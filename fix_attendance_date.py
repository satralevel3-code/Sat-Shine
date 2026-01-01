#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance, CustomUser
from django.utils import timezone
from datetime import date

# Find the user
user = CustomUser.objects.get(employee_id='MGJ00023')
print(f"Found user: {user}")

# Check existing attendance records
attendance_records = Attendance.objects.filter(user=user).order_by('-date')
print(f"Existing attendance records:")
for att in attendance_records:
    print(f"  Date: {att.date}, Status: {att.status}, Marked: {att.marked_at}")

# Fix the date if it's wrong (should be 2025-12-30)
correct_date = date(2025, 12, 30)
wrong_records = Attendance.objects.filter(user=user, date__gt=correct_date)

if wrong_records.exists():
    print(f"Found {wrong_records.count()} records with wrong dates. Fixing...")
    for record in wrong_records:
        print(f"  Fixing record from {record.date} to {correct_date}")
        record.date = correct_date
        record.save()
    print("Fixed attendance dates.")
else:
    print("No records need fixing.")

# Verify the fix
print("\nAfter fix:")
for att in Attendance.objects.filter(user=user).order_by('-date'):
    print(f"  Date: {att.date}, Status: {att.status}, Marked: {att.marked_at}")