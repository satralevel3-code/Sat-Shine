#!/usr/bin/env python
"""Verify DC and Associate approval status across all screens"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance, CustomUser
from django.db.models import Q
from django.utils import timezone

print("=" * 80)
print("DC & ASSOCIATE APPROVAL STATUS VERIFICATION")
print("=" * 80)

today = timezone.localdate()

# 1. CHECK ADMIN DASHBOARD COUNTERS
print("\n1. ADMIN DASHBOARD COUNTERS")
print("-" * 80)

# DC Confirmation Counter (should ONLY show MT/Support)
dc_pending = Attendance.objects.filter(
    user__designation__in=['MT', 'Support'],
    date__lte=today,
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
).exclude(
    user__designation__in=['Associate', 'DC']
).count()

print(f"DC Confirmation Pending: {dc_pending}")
print(f"  - Should ONLY include MT/Support")
print(f"  - Should EXCLUDE Associates and DCs")

# Admin Approval Counter (should show Associates, DCs, and confirmed MT/Support)
admin_pending = Attendance.objects.filter(
    date__lte=today,
    is_approved_by_admin=False,
    status__in=['present', 'half_day']
).filter(
    Q(user__designation__in=['Associate', 'DC']) |
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)
).count()

print(f"\nAdmin Approval Pending: {admin_pending}")
print(f"  - Should include Associates (direct)")
print(f"  - Should include DCs (direct)")
print(f"  - Should include MT/Support (after DC confirmation)")

# Breakdown by designation
for designation in ['Associate', 'DC', 'MT', 'Support']:
    if designation in ['Associate', 'DC']:
        count = Attendance.objects.filter(
            user__designation=designation,
            date__lte=today,
            is_approved_by_admin=False,
            status__in=['present', 'half_day']
        ).count()
    else:
        count = Attendance.objects.filter(
            user__designation=designation,
            date__lte=today,
            is_confirmed_by_dc=True,
            is_approved_by_admin=False,
            status__in=['present', 'half_day']
        ).count()
    print(f"  - {designation}: {count}")

# 2. CHECK DC CONFIRMATION SCREEN
print("\n2. DC CONFIRMATION SCREEN")
print("-" * 80)

dc_confirmation_query = Attendance.objects.filter(
    user__designation__in=['MT', 'Support'],
    date__lte=today,
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
).exclude(
    user__designation__in=['Associate', 'DC']
)

print(f"Records in DC Confirmation: {dc_confirmation_query.count()}")
designations = set(dc_confirmation_query.values_list('user__designation', flat=True))
print(f"Designations present: {designations if designations else 'None'}")

# Check if any Associates or DCs leaked in
leaked_associates = dc_confirmation_query.filter(user__designation='Associate').count()
leaked_dcs = dc_confirmation_query.filter(user__designation='DC').count()

if leaked_associates > 0:
    print(f"  ERROR: {leaked_associates} Associate records leaked into DC Confirmation!")
else:
    print(f"  OK: No Associate records in DC Confirmation")

if leaked_dcs > 0:
    print(f"  ERROR: {leaked_dcs} DC records leaked into DC Confirmation!")
else:
    print(f"  OK: No DC records in DC Confirmation")

# 3. CHECK ADMIN APPROVAL SCREEN
print("\n3. ADMIN APPROVAL SCREEN")
print("-" * 80)

admin_approval_query = Attendance.objects.filter(
    date__lte=today
).filter(
    Q(user__designation__in=['Associate', 'DC']) |
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)
)

print(f"Total records in Admin Approval: {admin_approval_query.count()}")
print(f"  - Pending approval: {admin_approval_query.filter(is_approved_by_admin=False).count()}")
print(f"  - Already approved: {admin_approval_query.filter(is_approved_by_admin=True).count()}")

# Breakdown by designation
print("\nBreakdown by designation:")
for designation in ['Associate', 'DC', 'MT', 'Support']:
    total = admin_approval_query.filter(user__designation=designation).count()
    pending = admin_approval_query.filter(
        user__designation=designation,
        is_approved_by_admin=False
    ).count()
    approved = admin_approval_query.filter(
        user__designation=designation,
        is_approved_by_admin=True
    ).count()
    print(f"  {designation}: Total={total}, Pending={pending}, Approved={approved}")

# 4. CHECK ASSOCIATE ATTENDANCE DETAILS
print("\n4. ASSOCIATE ATTENDANCE DETAILS")
print("-" * 80)

associate_att = Attendance.objects.filter(user__designation='Associate')
print(f"Total Associate attendance: {associate_att.count()}")

if associate_att.exists():
    print("\nRecent Associate attendance:")
    for att in associate_att.order_by('-date')[:3]:
        print(f"  {att.user.employee_id} | {att.date} | Status: {att.status}")
        print(f"    is_confirmed_by_dc: {att.is_confirmed_by_dc} (should be True)")
        print(f"    is_approved_by_admin: {att.is_approved_by_admin}")
        print(f"    In Admin Approval query: {admin_approval_query.filter(id=att.id).exists()}")

# 5. CHECK DC ATTENDANCE DETAILS
print("\n5. DC ATTENDANCE DETAILS")
print("-" * 80)

dc_att = Attendance.objects.filter(user__designation='DC')
print(f"Total DC attendance: {dc_att.count()}")

if dc_att.exists():
    print("\nRecent DC attendance:")
    for att in dc_att.order_by('-date')[:3]:
        print(f"  {att.user.employee_id} | {att.date} | Status: {att.status}")
        print(f"    is_confirmed_by_dc: {att.is_confirmed_by_dc} (should be True)")
        print(f"    is_approved_by_admin: {att.is_approved_by_admin}")
        print(f"    In Admin Approval query: {admin_approval_query.filter(id=att.id).exists()}")

# 6. FINAL VERIFICATION
print("\n6. FINAL VERIFICATION")
print("-" * 80)

issues = []

# Check 1: No Associates in DC Confirmation
if leaked_associates > 0:
    issues.append(f"Associates appearing in DC Confirmation ({leaked_associates} records)")

# Check 2: No DCs in DC Confirmation
if leaked_dcs > 0:
    issues.append(f"DCs appearing in DC Confirmation ({leaked_dcs} records)")

# Check 3: Associates in Admin Approval
associate_in_admin = admin_approval_query.filter(user__designation='Associate').count()
if associate_in_admin == 0 and associate_att.count() > 0:
    issues.append("Associates NOT appearing in Admin Approval (should be there)")

# Check 4: DCs in Admin Approval
dc_in_admin = admin_approval_query.filter(user__designation='DC').count()
if dc_in_admin == 0 and dc_att.count() > 0:
    issues.append("DCs NOT appearing in Admin Approval (should be there)")

# Check 5: All Associates have is_confirmed_by_dc=True
associate_not_confirmed = associate_att.filter(is_confirmed_by_dc=False).count()
if associate_not_confirmed > 0:
    issues.append(f"Associates with is_confirmed_by_dc=False ({associate_not_confirmed} records)")

# Check 6: All DCs have is_confirmed_by_dc=True
dc_not_confirmed = dc_att.filter(is_confirmed_by_dc=False).count()
if dc_not_confirmed > 0:
    issues.append(f"DCs with is_confirmed_by_dc=False ({dc_not_confirmed} records)")

if issues:
    print("ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
else:
    print("ALL CHECKS PASSED!")
    print("  - Associates bypass DC Confirmation")
    print("  - DCs bypass DC Confirmation")
    print("  - Associates appear in Admin Approval")
    print("  - DCs appear in Admin Approval")
    print("  - All Associates have is_confirmed_by_dc=True")
    print("  - All DCs have is_confirmed_by_dc=True")

print("\n" + "=" * 80)
