#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date

sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance

def test_simplified_dc():
    print("=== SIMPLIFIED DC CONFIRMATION TEST ===")
    
    dc_user = CustomUser.objects.filter(designation='DC').first()
    print(f"DC User: {dc_user.employee_id}")
    
    team_members = CustomUser.objects.filter(
        role='field_officer',
        dccb=dc_user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id)
    
    today = date.today()
    print(f"Date: {today}")
    print(f"Team Members: {team_members.count()}")
    
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        if attendance:
            print(f"{member.employee_id}: {attendance.status} | DC Confirmed: {attendance.is_confirmed_by_dc}")
        else:
            print(f"{member.employee_id}: No record")

if __name__ == "__main__":
    test_simplified_dc()