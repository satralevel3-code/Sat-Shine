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

def test_team_display():
    print("=== Team Display Test ===")
    
    # Find DC user
    dc_user = CustomUser.objects.filter(designation='DC').first()
    print(f"DC User: {dc_user.employee_id}")
    
    # Get team members (same logic as dashboard)
    team_users = CustomUser.objects.filter(
        role='field_officer',
        dccb=dc_user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id).order_by('employee_id')
    
    today = date.today()
    
    print(f"\\nTeam Members for {today}:")
    print("-" * 60)
    
    for user in team_users:
        user_attendance = Attendance.objects.filter(user=user, date=today).first()
        
        if user_attendance:
            status = user_attendance.status
            dc_confirmed = user_attendance.is_confirmed_by_dc
            print(f"{user.employee_id}: {status.upper()} | DC Confirmed: {dc_confirmed}")
        else:
            print(f"{user.employee_id}: NO RECORD | DC Confirmed: False")

if __name__ == "__main__":
    test_team_display()