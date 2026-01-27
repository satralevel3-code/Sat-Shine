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

print("=== Field Officer Dashboard Impact Check ===")

today = timezone.localdate()
print(f"Checking date: {today}")

# Get all field officers
field_officers = CustomUser.objects.filter(role='field_officer').order_by('employee_id')

print("\nField Officer Attendance Status:")
print("-" * 60)

for officer in field_officers:
    attendance = Attendance.objects.filter(user=officer, date=today).first()
    
    if attendance:
        status = attendance.status
        dc_confirmed = attendance.is_confirmed_by_dc
        confirmed_by = attendance.confirmed_by_dc.employee_id if attendance.confirmed_by_dc else "None"
        
        # Check what field officer sees vs admin sees
        field_view = status  # What field officer sees in their dashboard
        admin_view = status  # What admin sees
        
        if dc_confirmed and status == 'absent':
            admin_view = 'absent (DC Confirmed)'
        
        print(f"{officer.employee_id} ({officer.designation}):")
        print(f"  Status: {status}")
        print(f"  DC Confirmed: {dc_confirmed}")
        print(f"  Confirmed By: {confirmed_by}")
        print(f"  Field Officer Sees: {field_view}")
        print(f"  Admin Dashboard Sees: {admin_view}")
        print()
    else:
        print(f"{officer.employee_id} ({officer.designation}): No attendance record")
        print()

# Check attendance history impact
print("Attendance History Impact:")
print("-" * 40)

for officer in field_officers:
    recent_records = Attendance.objects.filter(user=officer).order_by('-date')[:5]
    
    if recent_records:
        print(f"{officer.employee_id} Recent Records:")
        for record in recent_records:
            dc_status = " [DC Confirmed]" if record.is_confirmed_by_dc else ""
            print(f"  {record.date}: {record.status}{dc_status}")
        print()

# Check team confirmation functionality
print("DC Team Confirmation Check:")
print("-" * 35)

dc_user = CustomUser.objects.filter(designation='DC').first()
if dc_user:
    print(f"DC User: {dc_user.employee_id}")
    
    team_members = CustomUser.objects.filter(
        role='field_officer',
        dccb=dc_user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id)
    
    print(f"Team Members: {[m.employee_id for m in team_members]}")
    
    # Check if DC can see team status
    print(f"\nDC Dashboard Team View:")
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        if attendance:
            confirmation_status = "Confirmed" if attendance.is_confirmed_by_dc else "Not Confirmed"
            print(f"  {member.employee_id}: {attendance.status} - {confirmation_status}")
        else:
            print(f"  {member.employee_id}: No Record - Can be confirmed as Absent")