#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone
import json

print("=== ATTENDANCE MARKING TEST ===\n")

# Get a field officer
field_officer = CustomUser.objects.filter(role='field_officer').first()
if not field_officer:
    print("No field officer found!")
    exit()

print(f"Testing with user: {field_officer.employee_id}")

# Check today's attendance
today = timezone.localdate()
existing = Attendance.objects.filter(user=field_officer, date=today).first()

if existing:
    print(f"Already marked: {existing.status} at {existing.check_in_time}")
else:
    print("No attendance marked for today")

# Test attendance creation
try:
    if not existing:
        test_attendance = Attendance.objects.create(
            user=field_officer,
            date=today,
            status='present',
            check_in_time=timezone.localtime().time(),
            latitude=23.0225,
            longitude=72.5714,
            location_accuracy=25.0,
            is_location_valid=True,
            location_address='Test Location',
            distance_from_office=100.0
        )
        print(f"[OK] Test attendance created: {test_attendance.id}")
        
        # Clean up
        test_attendance.delete()
        print("[OK] Test attendance cleaned up")
    else:
        print("[OK] Attendance model working (existing record found)")
        
except Exception as e:
    print(f"[ERROR] Error creating attendance: {e}")

print("\n=== TEST COMPLETE ===")
print("If this works locally, the issue is likely:")
print("1. CSRF token problems in production")
print("2. HTTPS/location permission issues")
print("3. Database connection issues")
print("4. Template inheritance problems")