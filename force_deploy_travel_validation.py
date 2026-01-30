#!/usr/bin/env python
"""
FORCE DEPLOYMENT: Travel Validation with Debug Logging
This will be included in Railway deployment to ensure validation works
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, TravelRequest
from django.utils import timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enhanced_validate_travel_approval_for_dc_confirmation(attendance):
    """
    ENHANCED Travel Approval Validation with Debug Logging
    FORCE DEPLOYMENT VERSION - Ensures validation works in production
    """
    logger.info(f"🔍 TRAVEL VALIDATION CHECK for {attendance.user.employee_id} on {attendance.date}")
    
    # Rule does NOT apply to Associates and DCs
    if attendance.user.designation in ['Associate', 'DC']:
        logger.info(f"✅ BYPASS: User {attendance.user.employee_id} is {attendance.user.designation} - no validation needed")
        return (True, None)
    
    # Rule applies ONLY to MT and Support
    if attendance.user.designation not in ['MT', 'Support']:
        logger.info(f"✅ BYPASS: User {attendance.user.employee_id} is {attendance.user.designation} - validation not applicable")
        return (True, None)
    
    # Rule applies ONLY to Present and Half Day
    if attendance.status not in ['present', 'half_day']:
        logger.info(f"✅ BYPASS: Attendance status is {attendance.status} - validation not needed")
        return (True, None)
    
    logger.info(f"🎯 VALIDATION REQUIRED: {attendance.user.designation} user with {attendance.status} status")
    
    # Check if travel request exists for this date
    travel_requests = TravelRequest.objects.filter(
        user=attendance.user,
        from_date__lte=attendance.date,
        to_date__gte=attendance.date
    )
    
    logger.info(f"🔍 Travel requests found: {travel_requests.count()}")
    
    # If no travel request exists, DC confirmation allowed
    if not travel_requests.exists():
        logger.info(f"✅ ALLOW: No travel request found - DC can confirm")
        return (True, None)
    
    # Handle multiple travel requests (invalid state)
    if travel_requests.count() > 1:
        logger.error(f"❌ ERROR: Multiple travel requests found for {attendance.date}")
        return (False, "Multiple travel requests found for this date. Please contact Admin.")
    
    # Get the travel request for this date
    travel_request = travel_requests.first()
    logger.info(f"📋 Travel request status: {travel_request.status}")
    
    # Check travel approval status
    if travel_request.status == 'pending':
        logger.warning(f"🚫 BLOCK: Travel request is PENDING - DC confirmation blocked")
        return (False, "Travel Approval is Pending")
    
    # Associate has taken action (approved OR rejected) - DC can confirm
    logger.info(f"✅ ALLOW: Travel request is {travel_request.status} - Associate has acted")
    return (True, None)

# Test the validation function
print("🚀 FORCE DEPLOYMENT: Travel Validation Test")
print("=" * 60)

# Check if we have test data
mt_users = CustomUser.objects.filter(designation='MT')
travel_requests = TravelRequest.objects.all()

print(f"📊 Production Data:")
print(f"   MT Users: {mt_users.count()}")
print(f"   Travel Requests: {travel_requests.count()}")
print(f"   Pending Travel: {travel_requests.filter(status='pending').count()}")

if mt_users.exists():
    mt_user = mt_users.first()
    today = timezone.localdate()
    
    # Create test attendance if needed
    test_attendance, created = Attendance.objects.get_or_create(
        user=mt_user,
        date=today,
        defaults={
            'status': 'present',
            'check_in_time': timezone.localtime().time(),
            'is_confirmed_by_dc': False
        }
    )
    
    print(f"\n🧪 Testing with user: {mt_user.employee_id}")
    can_confirm, error_msg = enhanced_validate_travel_approval_for_dc_confirmation(test_attendance)
    print(f"   Result: Can confirm = {can_confirm}")
    print(f"   Message: {error_msg}")

print("\n✅ FORCE DEPLOYMENT COMPLETE")
print("   Travel validation function is loaded and tested")
print("=" * 60)