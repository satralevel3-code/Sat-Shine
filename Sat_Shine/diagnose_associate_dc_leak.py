"""
Production Diagnostic: Check Associate Attendance in DC Confirmation Pipeline
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance, CustomUser
from django.utils import timezone
from datetime import timedelta

print("=" * 80)
print("PRODUCTION DIAGNOSTIC: Associate Attendance Leak Check")
print("=" * 80)

today = timezone.localdate()

# Check 1: Count all pending DC confirmations
print("\n1. CURRENT DC CONFIRMATION QUERY (WRONG - if includes Associates):")
wrong_query = Attendance.objects.filter(
    date__lte=today,
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
)
print(f"   Total records: {wrong_query.count()}")

# Show breakdown by designation
for designation in ['Associate', 'DC', 'MT', 'Support']:
    count = wrong_query.filter(user__designation=designation).count()
    if count > 0:
        print(f"   - {designation}: {count} records ❌" if designation in ['Associate', 'DC'] else f"   - {designation}: {count} records ✅")

# Check 2: Correct query (ONLY MT/Support)
print("\n2. CORRECT DC CONFIRMATION QUERY (ONLY MT/Support):")
correct_query = Attendance.objects.filter(
    user__designation__in=['MT', 'Support'],
    date__lte=today,
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
)
print(f"   Total records: {correct_query.count()}")

for designation in ['MT', 'Support']:
    count = correct_query.filter(user__designation=designation).count()
    print(f"   - {designation}: {count} records ✅")

# Check 3: Show Associate attendance that should NOT be in DC confirmation
print("\n3. ASSOCIATE ATTENDANCE (Should NEVER need DC confirmation):")
associate_attendance = Attendance.objects.filter(
    user__designation='Associate',
    date__lte=today,
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
)
print(f"   Total Associate records: {associate_attendance.count()}")

if associate_attendance.exists():
    print("\n   ⚠️  WARNING: Associate attendance found without DC confirmation!")
    print("   These should go DIRECTLY to Admin approval:")
    for att in associate_attendance[:5]:
        print(f"   - {att.user.employee_id} | {att.date} | {att.status}")

# Check 4: Admin approval query
print("\n4. ADMIN APPROVAL QUERY (Should include Associates + DCs + DC-confirmed MT/Support):")
from django.db.models import Q

admin_query = Attendance.objects.filter(
    date__lte=today,
    is_approved_by_admin=False,
    status__in=['present', 'half_day']
).filter(
    Q(user__designation__in=['Associate', 'DC']) |
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)
)
print(f"   Total records: {admin_query.count()}")

for designation in ['Associate', 'DC', 'MT', 'Support']:
    count = admin_query.filter(user__designation=designation).count()
    print(f"   - {designation}: {count} records")

# Check 5: Verify code deployment
print("\n5. CODE VERIFICATION:")
print("   Checking if latest code is deployed...")
print("   Expected: dc_confirmation view filters user__designation__in=['MT', 'Support']")
print("   Expected: approval_status view filters user__designation__in=['MT', 'Support']")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
if associate_attendance.count() > 0:
    print("❌ ISSUE CONFIRMED: Associate attendance appearing in DC confirmation pipeline")
    print("✅ FIX: Ensure Railway has deployed commit d769424 or later")
    print("✅ VERIFY: Check Railway deployment logs for latest commit hash")
else:
    print("✅ NO ISSUE: Associate attendance correctly bypassing DC confirmation")

print("\nTo fix in production:")
print("1. Verify Railway deployment: railway logs --tail 50")
print("2. Force redeploy: git commit --allow-empty -m 'Force redeploy' && git push")
print("3. Check Railway dashboard for active deployment")
print("=" * 80)
