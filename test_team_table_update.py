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

print("=== TEAM OVERVIEW TABLE UPDATE TEST ===")

# Clear today's records to simulate fresh state
today = timezone.localdate()
dc_user = CustomUser.objects.filter(designation='DC').first()
mt_users = CustomUser.objects.filter(designation='MT', dccb=dc_user.dccb)

print(f"DC User: {dc_user.employee_id}")
print(f"MT Users: {[u.employee_id for u in mt_users]}")
print(f"Date: {today}")

# Clear existing records
Attendance.objects.filter(user__in=mt_users, date=today).delete()
print("\nCleared existing attendance records")

# Show initial state (what DC sees in Team Overview table)
print(f"\nINITIAL STATE (Team Overview Table):")
print(f"{'Employee':<10} {'Status':<15} {'DC Confirmed':<12}")
print("-" * 40)

for member in mt_users:
    attendance = Attendance.objects.filter(user=member, date=today).first()
    
    if attendance:
        if attendance.status == 'present':
            status = "Present"
        elif attendance.status == 'absent':
            status = "Absent"
        elif attendance.status == 'half_day':
            status = "Half Day"
        else:
            status = "Not Marked"
    else:
        status = "Not Marked"
    
    dc_confirmed = "Done" if attendance and attendance.is_confirmed_by_dc else "Pending"
    
    print(f"{member.employee_id:<10} {status:<15} {dc_confirmed:<12}")

# Simulate DC confirmation
print(f"\n=== DC CLICKS 'CONFIRM ATTENDANCE' ===")

for member in mt_users:
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
    print(f"Processed {member.employee_id}: {attendance.status}, DC: {attendance.is_confirmed_by_dc}")

# Show updated state (what DC sees after confirmation)
print(f"\nUPDATED STATE (After Confirmation):")
print(f"{'Employee':<10} {'Status':<15} {'DC Confirmed':<12}")
print("-" * 40)

for member in mt_users:
    attendance = Attendance.objects.filter(user=member, date=today).first()
    
    if attendance:
        if attendance.status == 'present':
            status = "Present"
        elif attendance.status == 'absent':
            status = "Absent"
        elif attendance.status == 'half_day':
            status = "Half Day"
        else:
            status = "Not Marked"
    else:
        status = "Not Marked"
    
    dc_confirmed = "Done" if attendance and attendance.is_confirmed_by_dc else "Pending"
    
    print(f"{member.employee_id:<10} {status:<15} {dc_confirmed:<12}")

print(f"\n=== EXPECTED UI BEHAVIOR ===")
print(f"1. DC sees Team Overview table with 'Not Marked' and 'Pending' status")
print(f"2. DC clicks 'Confirm Attendance' button")
print(f"3. Button shows 'Processing...' with spinner")
print(f"4. Table updates in real-time:")
print(f"   - 'Not Marked' → 'Absent' (red badge)")
print(f"   - 'Pending' → 'Done' (green badge)")
print(f"5. Success message appears")
print(f"6. No page reload needed")

print(f"\n=== VERIFICATION ===")
print(f"Login as DC ({dc_user.employee_id}) and test the Team Overview functionality")