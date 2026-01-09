#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, AttendanceAuditLog
from datetime import date
from django.utils import timezone

print("=== FORCE DC CONFIRMATION FOR TODAY ===")

# Get today's date
today = timezone.localdate()
print(f"Today: {today}")

# Get DC and MT users
dc_user = CustomUser.objects.filter(designation='DC').first()
mt_users = CustomUser.objects.filter(designation='MT', dccb=dc_user.dccb)

print(f"DC User: {dc_user.employee_id}")
print(f"MT Users: {[u.employee_id for u in mt_users]}")

# Clear existing records for today
print("\nClearing existing records...")
Attendance.objects.filter(user__in=mt_users, date=today).delete()

# Force create DC confirmed records for today
print("\nCreating DC confirmed records...")
for mt_user in mt_users:
    attendance = Attendance.objects.create(
        user=mt_user,
        date=today,
        status='absent',
        is_confirmed_by_dc=True,
        confirmed_by_dc=dc_user,
        dc_confirmed_at=timezone.now(),
        confirmation_source='DC'
    )
    print(f"Created: {mt_user.employee_id} -> {attendance.status}, DC: {attendance.is_confirmed_by_dc}")

# Create audit log
audit = AttendanceAuditLog.objects.create(
    action_type='DC_CONFIRMATION',
    dc_user=dc_user,
    affected_employee_count=mt_users.count(),
    date_range_start=today,
    date_range_end=today,
    details=f'Force confirmation for {mt_users.count()} MT users'
)
print(f"\nAudit log created: {audit.id}")

# Verify records
print(f"\nVerification:")
for mt_user in mt_users:
    record = Attendance.objects.filter(user=mt_user, date=today).first()
    if record:
        print(f"{mt_user.employee_id}: {record.status}, DC: {record.is_confirmed_by_dc}, By: {record.confirmed_by_dc.employee_id}")
    else:
        print(f"{mt_user.employee_id}: NO RECORD")

print(f"\n=== INSTRUCTIONS ===")
print(f"1. Login as {mt_users[0].employee_id} (MT user)")
print(f"2. Go to field dashboard")
print(f"3. Should see: 'Absent (DC Confirmed by {dc_user.employee_id})'")
print(f"4. If still shows 'Not Marked', there's a template/frontend issue")

print(f"\nAlso test:")
print(f"- Admin dashboard should show 'A' badges")
print(f"- Attendance history should show DC confirmation")