#!/usr/bin/env python
"""Test DC attendance approval process"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance, CustomUser
from django.db.models import Q

print("=" * 80)
print("DC ATTENDANCE APPROVAL PROCESS TEST")
print("=" * 80)

# Get a DC attendance record
dc_att = Attendance.objects.filter(
    user__designation='DC',
    is_approved_by_admin=False
).first()

if not dc_att:
    print("\nNo pending DC attendance found for testing")
    exit()

print(f"\nTest Record:")
print(f"  Employee ID: {dc_att.user.employee_id}")
print(f"  Date: {dc_att.date}")
print(f"  Status: {dc_att.status}")
print(f"  is_confirmed_by_dc: {dc_att.is_confirmed_by_dc}")
print(f"  is_approved_by_admin: {dc_att.is_approved_by_admin}")

# Test the exact query from bulk_approve_attendance
print(f"\nTesting bulk_approve_attendance query:")

# Query 1: Basic filter
query1 = Attendance.objects.filter(
    id=dc_att.id,
    is_approved_by_admin=False
)
print(f"  Step 1 - Basic filter: {query1.exists()} (should be True)")

# Query 2: With designation filter (OLD - WRONG)
query2_old = query1.filter(
    Q(user__designation='Associate') |
    Q(user__designation__in=['DC', 'MT', 'Support'], is_confirmed_by_dc=True)
)
print(f"  Step 2 - OLD query with designation filter: {query2_old.exists()}")

# Query 3: Check individual conditions
print(f"\n  Checking individual conditions:")
print(f"    - Is Associate? {dc_att.user.designation == 'Associate'}")
print(f"    - Is DC? {dc_att.user.designation == 'DC'}")
print(f"    - is_confirmed_by_dc? {dc_att.is_confirmed_by_dc}")

# Query 4: Test DC-specific condition
dc_condition = query1.filter(
    user__designation='DC',
    is_confirmed_by_dc=True
)
print(f"    - DC with is_confirmed_by_dc=True: {dc_condition.exists()}")

# Query 5: Correct query (should include DC in Associate group)
query_correct = query1.filter(
    Q(user__designation__in=['Associate', 'DC']) |
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)
)
print(f"\n  Step 3 - CORRECT query (DC in Associate group): {query_correct.exists()}")

print(f"\n" + "=" * 80)
print("DIAGNOSIS:")
print("=" * 80)

if not query2_old.exists():
    print("\nISSUE FOUND: Current query is WRONG!")
    print("  Problem: DC is in the second condition which requires is_confirmed_by_dc=True")
    print("  Solution: Move DC to the first condition with Associate")
    print("\n  Current (WRONG):")
    print("    Q(user__designation='Associate') |")
    print("    Q(user__designation__in=['DC', 'MT', 'Support'], is_confirmed_by_dc=True)")
    print("\n  Should be (CORRECT):")
    print("    Q(user__designation__in=['Associate', 'DC']) |")
    print("    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)")
else:
    print("\nQuery is correct - DC attendance should be approvable")

print("=" * 80)
