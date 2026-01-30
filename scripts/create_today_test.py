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

print("=== Creating Test Data for Today ===")

today = timezone.localdate()
print(f"Today's date: {today}")

# Get users
dc_user = CustomUser.objects.filter(designation='DC').first()
team_members = CustomUser.objects.filter(
    role='field_officer',
    dccb=dc_user.dccb,
    designation__in=['MT', 'Support']
).exclude(id=dc_user.id)

print(f"DC User: {dc_user.employee_id}")
print(f"Team Members: {[m.employee_id for m in team_members]}")

# Create attendance records for today with DC confirmation
for member in team_members:
    attendance, created = Attendance.objects.get_or_create(
        user=member,
        date=today,
        defaults={
            'status': 'absent',
            'is_confirmed_by_dc': True,
            'confirmed_by_dc': dc_user,
            'dc_confirmed_at': timezone.now(),
            'confirmation_source': 'DC'
        }
    )
    
    if not created:
        attendance.status = 'absent'
        attendance.is_confirmed_by_dc = True
        attendance.confirmed_by_dc = dc_user
        attendance.dc_confirmed_at = timezone.now()
        attendance.save()
    
    print(f"Created/Updated: {member.employee_id} - Status: {attendance.status}, DC Confirmed: {attendance.is_confirmed_by_dc}")

print(f"\nNow check Admin Dashboard for date: {today}")
print("Should show 'A' (Absent) for team members with DC confirmation")