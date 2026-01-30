#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance
from django.utils import timezone

print("=== CREATING TEST DATA FOR DC CONFIRMATION ===\n")

# Create team members for the DC
dc_user = CustomUser.objects.filter(designation='DC').first()
if dc_user:
    print(f"DC User: {dc_user.employee_id} (DCCB: {dc_user.dccb})")
    
    # Update existing users to be in same DCCB as DC
    team_members = CustomUser.objects.filter(
        role='field_officer',
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id)
    
    for member in team_members:
        member.dccb = dc_user.dccb  # Assign same DCCB as DC
        member.save()
        print(f"Updated {member.employee_id} DCCB to {dc_user.dccb}")
    
    # Create some attendance records for testing
    today = timezone.localdate()
    
    for member in team_members:
        attendance, created = Attendance.objects.get_or_create(
            user=member,
            date=today,
            defaults={
                'status': 'present',
                'check_in_time': timezone.localtime().time(),
                'is_confirmed_by_dc': False
            }
        )
        
        if created:
            print(f"Created attendance for {member.employee_id}")
        else:
            print(f"Attendance already exists for {member.employee_id}")
    
    print(f"\nTeam setup complete:")
    print(f"DC: {dc_user.employee_id}")
    print(f"Team Members: {team_members.count()}")
    print(f"Same DCCB: {dc_user.dccb}")

else:
    print("No DC user found!")