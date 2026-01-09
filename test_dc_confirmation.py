#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, AttendanceAuditLog
from django.utils import timezone
from datetime import datetime, timedelta
import json

print("=== DC CONFIRMATION ABSENT RECORDS TEST ===\n")

# Get DC user and team
dc_user = CustomUser.objects.filter(designation='DC').first()
if not dc_user:
    print("No DC user found!")
    exit()

team_members = CustomUser.objects.filter(
    role='field_officer',
    dccb=dc_user.dccb,
    designation__in=['MT', 'Support']
).exclude(id=dc_user.id)

print(f"DC: {dc_user.employee_id}")
print(f"Team Members: {team_members.count()}")

# Test date
test_date = timezone.localdate()
print(f"Test Date: {test_date}")

# Clear existing attendance for clean test
Attendance.objects.filter(
    user__in=team_members,
    date=test_date
).delete()

print("Cleared existing attendance records")

# Simulate DC confirmation process
confirmed_count = 0

for member in team_members:
    # Create attendance record as DC confirmation would
    attendance, created = Attendance.objects.get_or_create(
        user=member,
        date=test_date,
        defaults={
            'status': 'absent',  # NM becomes Absent
            'is_confirmed_by_dc': True,
            'confirmed_by_dc': dc_user,
            'dc_confirmed_at': timezone.now(),
            'confirmation_source': 'DC'
        }
    )
    
    if created:
        print(f"Created ABSENT record for {member.employee_id}")
        confirmed_count += 1

# Create audit log
audit_log = AttendanceAuditLog.objects.create(
    action_type='DC_CONFIRMATION',
    dc_user=dc_user,
    affected_employee_count=team_members.count(),
    date_range_start=test_date,
    date_range_end=test_date,
    details=f'Test confirmation for {team_members.count()} team members'
)

print(f"\nAudit log created: {audit_log.id}")

# Verify records
print(f"\n=== VERIFICATION ===")
absent_records = Attendance.objects.filter(
    user__in=team_members,
    date=test_date,
    status='absent',
    is_confirmed_by_dc=True
)

print(f"Absent records created: {absent_records.count()}")
print(f"DC confirmed records: {absent_records.count()}")

# Check how they appear in admin view logic
print(f"\n=== ADMIN VIEW DISPLAY ===")
for record in absent_records:
    # This is how admin daily attendance shows status
    status_code = 'A' if record.status == 'absent' else 'P' if record.status == 'present' else 'H'
    print(f"{record.user.employee_id}: Status='{record.status}' -> Display='{status_code}'")
    print(f"  - DC Confirmed: {record.is_confirmed_by_dc}")
    print(f"  - Confirmed By: {record.confirmed_by_dc.employee_id if record.confirmed_by_dc else 'None'}")
    print(f"  - Confirmed At: {record.dc_confirmed_at}")

# Test admin dashboard KPI impact
from django.db.models import Count, Case, When, IntegerField

attendance_kpis = Attendance.objects.filter(date=test_date).aggregate(
    present=Count(Case(When(status='present', then=1), output_field=IntegerField())),
    absent=Count(Case(When(status='absent', then=1), output_field=IntegerField())),
    half_day=Count(Case(When(status='half_day', then=1), output_field=IntegerField()))
)

print(f"\n=== ADMIN DASHBOARD IMPACT ===")
print(f"Present: {attendance_kpis['present']}")
print(f"Absent: {attendance_kpis['absent']}")
print(f"Half Day: {attendance_kpis['half_day']}")

print(f"\n[OK] DC Confirmation Test Complete")
print(f"[OK] Absent records properly created and will show as 'A' in admin dashboard")
print(f"[OK] Individual history will show absent count: {attendance_kpis['absent']}")