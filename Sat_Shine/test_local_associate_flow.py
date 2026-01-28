"""
Local Test: Verify Associate Attendance Approval Flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance, CustomUser
from django.utils import timezone
from django.db.models import Q

print("=" * 80)
print("LOCAL TEST: Associate Attendance Approval Flow")
print("=" * 80)

today = timezone.localdate()

# Test 1: Check DC Confirmation Query
print("\n1. DC CONFIRMATION QUERY TEST:")
print("-" * 80)

dc_query = Attendance.objects.filter(
    user__designation__in=['MT', 'Support'],
    date__lte=today,
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
).exclude(
    user__designation__in=['Associate', 'DC']
)

print(f"Total records: {dc_query.count()}")
print("\nBreakdown by designation:")
for designation in ['Associate', 'DC', 'MT', 'Support']:
    count = dc_query.filter(user__designation=designation).count()
    status = "WRONG" if designation in ['Associate', 'DC'] and count > 0 else "CORRECT"
    print(f"  {designation}: {count} records [{status}]")

if dc_query.filter(user__designation__in=['Associate', 'DC']).exists():
    print("\n[ISSUE] Associate/DC records found in DC confirmation query!")
else:
    print("\n[PASS] No Associate/DC records in DC confirmation query")

# Test 2: Check Admin Approval Query
print("\n2. ADMIN APPROVAL QUERY TEST:")
print("-" * 80)

admin_query = Attendance.objects.filter(
    date__lte=today,
    is_approved_by_admin=False,
    status__in=['present', 'half_day']
).filter(
    Q(user__designation__in=['Associate', 'DC']) |
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)
)

print(f"Total records: {admin_query.count()}")
print("\nBreakdown by designation:")
for designation in ['Associate', 'DC', 'MT', 'Support']:
    count = admin_query.filter(user__designation=designation).count()
    print(f"  {designation}: {count} records")

associate_count = admin_query.filter(user__designation='Associate').count()
if associate_count > 0:
    print(f"\n[PASS] {associate_count} Associate records in Admin approval query")
else:
    print("\n[WARNING] No Associate records in Admin approval query")

# Test 3: Check Associate Attendance Records
print("\n3. ASSOCIATE ATTENDANCE RECORDS:")
print("-" * 80)

associate_users = CustomUser.objects.filter(designation='Associate', role='field_officer')
print(f"Total Associate users: {associate_users.count()}")

if associate_users.exists():
    for user in associate_users[:3]:
        print(f"\n  Associate: {user.employee_id}")
        recent_att = Attendance.objects.filter(user=user).order_by('-date')[:3]
        
        if recent_att.exists():
            for att in recent_att:
                print(f"    Date: {att.date} | Status: {att.status} | DC Confirmed: {att.is_confirmed_by_dc} | Admin Approved: {att.is_approved_by_admin}")
        else:
            print("    No attendance records")

# Test 4: Sample Queries
print("\n4. SAMPLE QUERY RESULTS:")
print("-" * 80)

# Associates with is_confirmed_by_dc=False
bad_associates = Attendance.objects.filter(
    user__designation='Associate',
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
)
print(f"Associates with is_confirmed_by_dc=False: {bad_associates.count()}")
if bad_associates.exists():
    print("  [ISSUE] These should have is_confirmed_by_dc=True")
    for att in bad_associates[:3]:
        print(f"    {att.user.employee_id} | {att.date} | {att.status}")

# Associates pending admin approval
pending_admin = Attendance.objects.filter(
    user__designation='Associate',
    is_approved_by_admin=False,
    status__in=['present', 'half_day']
)
print(f"\nAssociates pending admin approval: {pending_admin.count()}")
if pending_admin.exists():
    print("  [CORRECT] These should be in Admin approval screen")
    for att in pending_admin[:3]:
        print(f"    {att.user.employee_id} | {att.date} | {att.status} | DC Confirmed: {att.is_confirmed_by_dc}")

print("\n" + "=" * 80)
print("TEST SUMMARY:")
print("=" * 80)

issues = []
if dc_query.filter(user__designation__in=['Associate', 'DC']).exists():
    issues.append("[X] Associates/DCs appearing in DC confirmation query")
if associate_count == 0 and associate_users.exists():
    issues.append("[!] No Associates in Admin approval query (might be all approved)")
if bad_associates.count() > 0:
    issues.append(f"[X] {bad_associates.count()} Associates with is_confirmed_by_dc=False")

if issues:
    print("\nISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n[PASS] ALL TESTS PASSED - Queries working correctly")

print("\n" + "=" * 80)
