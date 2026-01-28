#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date

# Add the project directory to Python path
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance

def debug_dc_status():
    print("=== DC Status Debug ===")
    
    # Find DC user
    dc_user = CustomUser.objects.filter(designation='DC').first()
    if not dc_user:
        print("No DC user found!")
        return
    
    print(f"DC User: {dc_user.employee_id} - {dc_user.first_name}")
    
    # Find team members
    team_members = CustomUser.objects.filter(
        role='field_officer',
        dccb=dc_user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id)
    
    print(f"Team Members: {team_members.count()}")
    
    today = date.today()
    print(f"Checking date: {today}")
    
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        if attendance:
            print(f"{member.employee_id}: Status={attendance.status}, DC_Confirmed={attendance.is_confirmed_by_dc}")
        else:
            print(f"{member.employee_id}: No attendance record")

if __name__ == "__main__":
    debug_dc_status()