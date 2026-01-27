#!/usr/bin/env python
"""
Production verification script for Associate travel approval
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest

def verify_production_setup():
    print("=== Production Associate Travel Approval Verification ===\n")
    
    # 1. Check MGJ00002 setup
    try:
        associate = CustomUser.objects.get(employee_id='MGJ00002')
        print(f"MGJ00002 Status:")
        print(f"  Name: {associate.first_name} {associate.last_name}")
        print(f"  Designation: {associate.designation}")
        print(f"  Can Approve Travel: {associate.can_approve_travel}")
        print(f"  Is Active: {associate.is_active}")
        print(f"  Assigned DCCBs: {associate.multiple_dccb}")
        print()
        
        # 2. Check travel requests visible to MGJ00002
        if associate.multiple_dccb:
            visible_requests = TravelRequest.objects.filter(
                user__dccb__in=associate.multiple_dccb
            ).order_by('-created_at')
            
            print(f"Travel Requests Visible to MGJ00002: {visible_requests.count()}")
            for tr in visible_requests[:5]:  # Show first 5
                print(f"  ID: {tr.id} | {tr.user.employee_id} ({tr.user.dccb}) | {tr.status} | {tr.from_date}")
            print()
            
            # 3. Check pending requests specifically
            pending_requests = visible_requests.filter(status='pending')
            print(f"Pending Travel Requests for MGJ00002: {pending_requests.count()}")
            for tr in pending_requests:
                print(f"  PENDING: {tr.user.employee_id} | {tr.from_date} to {tr.to_date} | {tr.purpose[:50]}...")
            print()
        
        # 4. Check URL access requirements
        print("URL Access Check:")
        print(f"  Designation == 'Associate': {'PASS' if associate.designation == 'Associate' else 'FAIL'}")
        print(f"  can_approve_travel == True: {'PASS' if associate.can_approve_travel else 'FAIL'}")
        print(f"  is_active == True: {'PASS' if associate.is_active else 'FAIL'}")
        print(f"  has_multiple_dccb: {'PASS' if associate.multiple_dccb else 'FAIL'}")
        print()
        
        # 5. Test travel approval view logic
        print("Travel Approval View Logic Test:")
        if associate.designation == 'Associate' and associate.multiple_dccb:
            user_dccbs = associate.multiple_dccb
            test_requests = TravelRequest.objects.filter(
                user__dccb__in=user_dccbs,
                status='pending'
            )
            print(f"  Requests that should appear in approval screen: {test_requests.count()}")
            
            # Check if any MT/DC/Support users from assigned DCCBs have travel requests
            from datetime import date, timedelta
            today = date.today()
            recent_requests = TravelRequest.objects.filter(
                user__dccb__in=user_dccbs,
                user__designation__in=['MT', 'DC', 'Support'],
                created_at__gte=today - timedelta(days=30)
            )
            print(f"  Recent requests from MT/DC/Support in assigned DCCBs: {recent_requests.count()}")
        
        # 6. Production URLs to test
        print("\nProduction URLs to Test:")
        print("  Login: https://your-domain.com/auth/login/")
        print("  Associate Dashboard: https://your-domain.com/auth/associate-dashboard/")
        print("  Travel Approvals: https://your-domain.com/auth/associate-travel-approvals/")
        print()
        
        # 7. Test credentials
        print("Test Credentials:")
        print("  Username: MGJ00002")
        print("  Password: SatShine@2024")
        print()
        
        # 8. Expected behavior
        print("Expected Behavior in Production:")
        print("  1. Login with MGJ00002 should redirect to Associate dashboard")
        print("  2. Associate dashboard should show 'Travel Approvals' section")
        print("  3. Travel Approvals page should show requests from assigned DCCBs")
        print("  4. Should be able to approve/reject pending requests")
        print("  5. Notifications should be sent after approval/rejection")
        
        if associate.designation == 'Associate' and associate.can_approve_travel and associate.multiple_dccb:
            print("\n✅ MGJ00002 is correctly configured for travel approvals!")
        else:
            print("\n❌ MGJ00002 configuration issues detected!")
            
    except CustomUser.DoesNotExist:
        print("❌ MGJ00002 not found in database!")
    
    # 9. Check other Associates for comparison
    print("\n=== Other Associates Comparison ===")
    other_associates = CustomUser.objects.filter(designation='Associate', is_active=True).exclude(employee_id='MGJ00002')
    for assoc in other_associates:
        print(f"{assoc.employee_id}: {assoc.multiple_dccb} | Can Approve: {assoc.can_approve_travel}")

if __name__ == '__main__':
    verify_production_setup()