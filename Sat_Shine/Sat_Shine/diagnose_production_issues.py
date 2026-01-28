#!/usr/bin/env python
"""
Comprehensive production diagnostic for Associate travel approval issues
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.urls import reverse
from django.test import Client

def diagnose_associate_production_issues():
    print("=== Associate Production Issue Diagnosis ===\n")
    
    # 1. Check MGJ00002 complete setup
    try:
        associate = CustomUser.objects.get(employee_id='MGJ00002')
        print("1. MGJ00002 Configuration:")
        print(f"   Employee ID: {associate.employee_id}")
        print(f"   Username: {associate.username}")
        print(f"   First Name: {associate.first_name}")
        print(f"   Last Name: {associate.last_name}")
        print(f"   Email: {associate.email}")
        print(f"   Role: {associate.role}")
        print(f"   Designation: {associate.designation}")
        print(f"   Is Active: {associate.is_active}")
        print(f"   Is Staff: {associate.is_staff}")
        print(f"   Is Superuser: {associate.is_superuser}")
        print(f"   Can Approve Travel: {associate.can_approve_travel}")
        print(f"   Role Level: {associate.role_level}")
        print(f"   Multiple DCCBs: {associate.multiple_dccb}")
        print(f"   DCCB: {associate.dccb}")
        print()
        
        # 2. Check password and login capability
        print("2. Login Test:")
        client = Client()
        login_response = client.post('/auth/login/', {
            'employee_id': 'MGJ00002',
            'password': 'SatShine@2024'
        })
        print(f"   Login Status Code: {login_response.status_code}")
        print(f"   Login Redirect: {login_response.get('Location', 'No redirect')}")
        
        # Check if user can authenticate
        from django.contrib.auth import authenticate
        auth_user = authenticate(username='MGJ00002', password='SatShine@2024')
        print(f"   Authentication: {'SUCCESS' if auth_user else 'FAILED'}")
        print()
        
        # 3. Check URL access
        print("3. URL Access Test:")
        try:
            from authe.urls import urlpatterns
            print("   authe.urls imported: SUCCESS")
            
            # Check if associate_travel_approvals URL exists
            from django.urls import reverse
            try:
                url = reverse('associate_travel_approvals')
                print(f"   associate_travel_approvals URL: {url}")
            except:
                print("   associate_travel_approvals URL: NOT FOUND")
            
            # Check travel views
            from authe import travel_views
            print("   travel_views imported: SUCCESS")
            
            # Check if associate_travel_approvals function exists
            if hasattr(travel_views, 'associate_travel_approvals'):
                print("   associate_travel_approvals function: EXISTS")
            else:
                print("   associate_travel_approvals function: MISSING")
                
        except Exception as e:
            print(f"   URL/View Error: {e}")
        print()
        
        # 4. Check travel requests data
        print("4. Travel Requests Analysis:")
        all_requests = TravelRequest.objects.all().order_by('-created_at')
        print(f"   Total Travel Requests: {all_requests.count()}")
        
        # Check requests for MGJ00002's DCCBs
        if associate.multiple_dccb:
            assigned_requests = TravelRequest.objects.filter(
                user__dccb__in=associate.multiple_dccb
            ).order_by('-created_at')
            print(f"   Requests for Assigned DCCBs: {assigned_requests.count()}")
            
            pending_requests = assigned_requests.filter(status='pending')
            print(f"   Pending Requests: {pending_requests.count()}")
            
            for req in pending_requests[:3]:
                print(f"     - {req.user.employee_id} ({req.user.dccb}) | {req.from_date} | {req.status}")
        print()
        
        # 5. Check view permissions
        print("5. View Permission Test:")
        from authe.travel_views import associate_travel_approvals
        
        # Simulate request
        from django.http import HttpRequest
        from django.contrib.auth.models import AnonymousUser
        
        request = HttpRequest()
        request.user = associate
        request.method = 'GET'
        
        try:
            # Test if view can be called
            print("   View callable: Testing...")
            # Don't actually call it, just check if it exists and is callable
            if callable(associate_travel_approvals):
                print("   View callable: SUCCESS")
            else:
                print("   View callable: FAILED")
        except Exception as e:
            print(f"   View callable: ERROR - {e}")
        print()
        
        # 6. Check database queries that the view would make
        print("6. Database Query Test:")
        try:
            # Simulate the query from associate_travel_approvals view
            from datetime import date, timedelta
            today = date.today()
            from_date = today
            to_date = today + timedelta(days=30)
            
            if associate.designation == 'Associate':
                user_dccbs = associate.multiple_dccb or []
                travel_requests = TravelRequest.objects.filter(
                    user__dccb__in=user_dccbs,
                    from_date__range=[from_date, to_date]
                ).select_related('user')
                
                print(f"   Query Result Count: {travel_requests.count()}")
                print(f"   User DCCBs: {user_dccbs}")
                
                for req in travel_requests[:3]:
                    print(f"     - ID: {req.id} | {req.user.employee_id} | {req.status}")
            else:
                print("   User is not Associate - query would fail")
        except Exception as e:
            print(f"   Database Query Error: {e}")
        print()
        
        # 7. Check for any blocking conditions
        print("7. Blocking Conditions Check:")
        
        # Check if user is in correct role
        if associate.role != 'field_officer':
            print(f"   ISSUE: Role is '{associate.role}', should be 'field_officer'")
        else:
            print("   Role: OK")
            
        # Check if designation is correct
        if associate.designation != 'Associate':
            print(f"   ISSUE: Designation is '{associate.designation}', should be 'Associate'")
        else:
            print("   Designation: OK")
            
        # Check if can_approve_travel is enabled
        if not associate.can_approve_travel:
            print("   ISSUE: can_approve_travel is False")
        else:
            print("   Can Approve Travel: OK")
            
        # Check if multiple_dccb is set
        if not associate.multiple_dccb:
            print("   ISSUE: multiple_dccb is empty")
        else:
            print("   Multiple DCCBs: OK")
            
        # Check if user is active
        if not associate.is_active:
            print("   ISSUE: User is not active")
        else:
            print("   User Active: OK")
        print()
        
        # 8. Production URLs to test manually
        print("8. Manual Testing URLs:")
        print("   Login: https://your-domain.com/auth/login/")
        print("   Dashboard: https://your-domain.com/auth/associate-dashboard/")
        print("   Travel Approvals: https://your-domain.com/auth/associate-travel-approvals/")
        print()
        print("   Test Steps:")
        print("   1. Login with MGJ00002 / SatShine@2024")
        print("   2. Check if redirected to associate dashboard")
        print("   3. Look for 'Travel Approvals' section")
        print("   4. Click on Travel Approvals link")
        print("   5. Check if travel requests are visible")
        print("   6. Try to approve/reject a request")
        print()
        
        # 9. Potential fixes
        print("9. Potential Issues & Fixes:")
        
        issues_found = []
        
        if associate.role != 'field_officer':
            issues_found.append("Role should be 'field_officer'")
            
        if associate.designation != 'Associate':
            issues_found.append("Designation should be 'Associate'")
            
        if not associate.can_approve_travel:
            issues_found.append("can_approve_travel should be True")
            
        if not associate.multiple_dccb:
            issues_found.append("multiple_dccb should not be empty")
            
        if not associate.is_active:
            issues_found.append("User should be active")
            
        if issues_found:
            print("   ISSUES FOUND:")
            for issue in issues_found:
                print(f"     - {issue}")
            print("\n   Run fix script to resolve these issues")
        else:
            print("   No configuration issues found")
            print("   Issue might be in:")
            print("     - URL routing")
            print("     - Template rendering")
            print("     - JavaScript/Frontend")
            print("     - Production environment settings")
        
    except CustomUser.DoesNotExist:
        print("CRITICAL: MGJ00002 not found in database!")
        print("Need to create or fix MGJ00002 user")
    
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnose_associate_production_issues()