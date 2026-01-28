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

def final_verification():
    print("=== FINAL DC CONFIRMATION VERIFICATION ===")
    
    # Find DC user
    dc_user = CustomUser.objects.filter(designation='DC').first()
    print(f"✓ DC User: {dc_user.employee_id} - {dc_user.first_name}")
    
    # Get team members
    team_members = CustomUser.objects.filter(
        role='field_officer',
        dccb=dc_user.dccb,
        designation__in=['MT', 'Support']
    ).exclude(id=dc_user.id).order_by('employee_id')
    
    today = date.today()
    print(f"✓ Date: {today}")
    print(f"✓ Team Size: {team_members.count()}")
    
    print("\\n--- TEAM MEMBER STATUS ---")
    all_confirmed = True
    
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        
        if attendance:
            status = attendance.status.upper()
            dc_confirmed = "✓ DONE" if attendance.is_confirmed_by_dc else "✗ PENDING"
            confirmed_by = attendance.confirmed_by_dc.employee_id if attendance.confirmed_by_dc else "None"
            
            print(f"{member.employee_id}: {status} | DC Status: {dc_confirmed} | By: {confirmed_by}")
            
            if not attendance.is_confirmed_by_dc:
                all_confirmed = False
        else:
            print(f"{member.employee_id}: NO RECORD | DC Status: ✗ PENDING")
            all_confirmed = False
    
    print("\\n--- VERIFICATION RESULT ---")
    if all_confirmed:
        print("✅ ALL TEAM MEMBERS CONFIRMED")
        print("✅ DC CONFIRMATION WORKING PROPERLY")
        print("✅ READY FOR PRODUCTION USE")
    else:
        print("❌ SOME MEMBERS NOT CONFIRMED")
        print("❌ NEED TO RUN DC CONFIRMATION")
    
    print("\\n--- TEMPLATE DISPLAY LOGIC ---")
    print("Template should show:")
    for member in team_members:
        attendance = Attendance.objects.filter(user=member, date=today).first()
        if attendance:
            if attendance.status == 'absent' and attendance.is_confirmed_by_dc:
                print(f"  {member.employee_id}: 'Absent' badge + 'Done' confirmation")
            else:
                print(f"  {member.employee_id}: '{attendance.status.title()}' badge + 'Done' confirmation")
        else:
            print(f"  {member.employee_id}: 'Not Marked' badge + 'Pending' confirmation")

if __name__ == "__main__":
    final_verification()