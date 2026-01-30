"""
CRITICAL DATA FIX: Remove Associate/DC from DC Confirmation Pipeline
Run this ONCE in production to fix corrupted data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import Attendance
from django.db import transaction

print("=" * 80)
print("CRITICAL DATA FIX: Associate/DC DC Confirmation Cleanup")
print("=" * 80)

# Check current state
print("\n1. BEFORE FIX - Checking corrupted records:")
corrupted_records = Attendance.objects.filter(
    user__designation__in=['Associate', 'DC'],
    is_confirmed_by_dc=False,
    status__in=['present', 'half_day']
)

print(f"   Total corrupted records: {corrupted_records.count()}")

if corrupted_records.exists():
    print("\n   Breakdown by designation:")
    for designation in ['Associate', 'DC']:
        count = corrupted_records.filter(user__designation=designation).count()
        if count > 0:
            print(f"   - {designation}: {count} records")
    
    print("\n   Sample records (first 5):")
    for att in corrupted_records[:5]:
        print(f"   - {att.user.employee_id} ({att.user.designation}) | {att.date} | {att.status}")
    
    # Fix the data
    print("\n2. APPLYING FIX...")
    with transaction.atomic():
        # For Associates and DCs, set DC confirmation as not required
        # They should go directly to admin approval
        updated_count = corrupted_records.update(
            is_confirmed_by_dc=True,  # Mark as "confirmed" so they skip DC pipeline
            confirmed_by_dc=None,  # No DC confirmed them
            dc_confirmed_at=None,  # No confirmation timestamp
        )
        
        print(f"   ✅ Updated {updated_count} records")
        print("   - Set is_confirmed_by_dc=True (to skip DC pipeline)")
        print("   - Cleared confirmed_by_dc and dc_confirmed_at")
    
    # Verify fix
    print("\n3. AFTER FIX - Verification:")
    still_corrupted = Attendance.objects.filter(
        user__designation__in=['Associate', 'DC'],
        is_confirmed_by_dc=False,
        status__in=['present', 'half_day']
    ).count()
    
    if still_corrupted == 0:
        print("   ✅ SUCCESS: No more Associate/DC records in DC confirmation pipeline")
    else:
        print(f"   ❌ WARNING: Still {still_corrupted} corrupted records found")
    
    # Check admin approval pipeline
    admin_pending = Attendance.objects.filter(
        user__designation__in=['Associate', 'DC'],
        is_approved_by_admin=False,
        status__in=['present', 'half_day']
    ).count()
    
    print(f"\n4. ADMIN APPROVAL PIPELINE:")
    print(f"   Associate/DC records pending admin approval: {admin_pending}")
    print("   ✅ These records are now correctly in admin approval pipeline")
    
else:
    print("   ✅ No corrupted records found - data is clean!")

print("\n" + "=" * 80)
print("FIX COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. Verify DC Confirmation screen shows ONLY MT/Support")
print("2. Verify Admin Approval screen shows Associates/DCs")
print("3. Test new Associate attendance marking")
print("=" * 80)
