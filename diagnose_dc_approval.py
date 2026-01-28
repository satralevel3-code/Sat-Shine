#!/usr/bin/env python
"""Diagnose DC attendance approval issue"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance, CustomUser
from django.db.models import Q
from django.utils import timezone

print("=" * 60)
print("DC ATTENDANCE APPROVAL DIAGNOSTIC")
print("=" * 60)

# Find all DC users
dc_users = CustomUser.objects.filter(designation='DC')
print(f"\nTotal DC users: {dc_users.count()}")
for dc in dc_users:
    print(f"  - {dc.employee_id}: {dc.first_name} {dc.last_name}")

# Find all DC attendance records
dc_attendance = Attendance.objects.filter(user__designation='DC')
print(f"\nTotal DC attendance records: {dc_attendance.count()}")

# Check DC attendance that should appear in admin approval
today = timezone.localdate()
admin_approval_query = Attendance.objects.filter(
    user__designation='DC',
    date__lte=today
)

print(f"\nDC attendance (all): {admin_approval_query.count()}")
print(f"  - Pending admin approval: {admin_approval_query.filter(is_approved_by_admin=False).count()}")
print(f"  - Already approved: {admin_approval_query.filter(is_approved_by_admin=True).count()}")

# Check is_confirmed_by_dc status
print(f"\nDC attendance by DC confirmation status:")
print(f"  - is_confirmed_by_dc=True: {admin_approval_query.filter(is_confirmed_by_dc=True).count()}")
print(f"  - is_confirmed_by_dc=False: {admin_approval_query.filter(is_confirmed_by_dc=False).count()}")

# Show recent DC attendance details
print(f"\nRecent DC attendance records:")
recent_dc = admin_approval_query.order_by('-date')[:5]
for att in recent_dc:
    print(f"  {att.user.employee_id} | {att.date} | Status: {att.status} | "
          f"DC Confirmed: {att.is_confirmed_by_dc} | Admin Approved: {att.is_approved_by_admin}")

# Test the exact query from admin_approval view
print(f"\nTesting admin_approval view query:")
base_query = Attendance.objects.filter(
    date__lte=today
).filter(
    Q(user__designation__in=['Associate', 'DC']) |
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)
)

dc_in_query = base_query.filter(user__designation='DC')
print(f"  - DC records in admin approval query: {dc_in_query.count()}")
print(f"  - DC pending approval: {dc_in_query.filter(is_approved_by_admin=False).count()}")

if dc_in_query.exists():
    print(f"\nDC attendance IS appearing in admin approval query")
else:
    print(f"\nDC attendance NOT appearing in admin approval query")
    print(f"   Possible reasons:")
    print(f"   1. No DC attendance records exist")
    print(f"   2. All DC attendance already approved")
    print(f"   3. Query logic issue")

print("\n" + "=" * 60)
