#!/usr/bin/env python
"""
Local Travel Request Debug & Test Script
Test the complete travel request workflow locally
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.db import transaction
from django.utils import timezone
from django.test import Client
from django.urls import reverse
import json

def test_local_travel_system():
    print("=== LOCAL TRAVEL REQUEST SYSTEM TEST ===\n")
    
    # 1. Setup Test Users
    print("1. Setting up test users...")
    
    with transaction.atomic():
        # Create Associate user
        associate, created = CustomUser.objects.get_or_create(
            employee_id='MP0001',
            defaults={
                'email': 'associate@test.com',
                'first_name': 'TEST',
                'last_name': 'ASSOCIATE',
                'designation': 'Associate',
                'role': 'admin',
                'contact_number': '9999999999',
                'multiple_dccb': ['AHMEDABAD', 'BARODA', 'BHARUCH'],
                'can_approve_travel': True,
                'role_level': 7,
                'is_active': True
            }
        )
        
        if created:
            associate.set_password('test123')
            associate.save()
            print(f"   [OK] Created Associate: {associate.employee_id}")
        else:
            associate.multiple_dccb = ['AHMEDABAD', 'BARODA', 'BHARUCH']
            associate.can_approve_travel = True
            associate.role_level = 7
            associate.set_password('test123')
            associate.save()
            print(f"   [OK] Updated Associate: {associate.employee_id}")
        
        # Create Field Officer user
        field_user, created = CustomUser.objects.get_or_create(
            employee_id='MGJ00001',
            defaults={
                'email': 'field@test.com',
                'first_name': 'TEST',
                'last_name': 'FIELD',
                'designation': 'MT',
                'role': 'field_officer',
                'contact_number': '8888888888',
                'dccb': 'AHMEDABAD',
                'is_active': True
            }
        )
        
        if created:
            field_user.set_password('test123')
            field_user.save()
            print(f"   [OK] Created Field User: {field_user.employee_id}")
        else:
            field_user.dccb = 'AHMEDABAD'
            field_user.designation = 'MT'
            field_user.set_password('test123')
            field_user.save()
            print(f"   [OK] Updated Field User: {field_user.employee_id}")
    
    # 2. Create Test Travel Request
    print("\n2. Creating test travel request...")
    
    # Clear existing test requests
    TravelRequest.objects.filter(er_id__startswith='TEST').delete()
    
    test_request = TravelRequest.objects.create(
        user=field_user,
        from_date=timezone.localdate(),
        to_date=timezone.localdate() + timedelta(days=1),
        duration='full_day',
        days_count=1.0,
        request_to=associate,
        er_id='TEST12345678901234567',
        distance_km=50,
        address='Test Address for Local Testing Purpose Only',
        contact_person='9876543210',
        purpose='Test travel request for local system verification and testing'
    )
    
    print(f"   [OK] Created travel request ID: {test_request.id}")
    print(f"   Request details:")
    print(f"     - User: {test_request.user.employee_id} ({test_request.user.dccb})")
    print(f"     - Assigned to: {test_request.request_to.employee_id}")
    print(f"     - Status: {test_request.status}")
    
    # 3. Test Associate Dashboard Access
    print("\n3. Testing Associate dashboard access...")
    
    client = Client()
    
    # Login as Associate
    login_success = client.login(username='MP0001', password='test123')
    print(f"   Associate login success: {login_success}")
    
    if login_success:
        # Test dashboard access
        try:
            response = client.get('/auth/associate-dashboard/')
            print(f"   Dashboard response status: {response.status_code}")
            
            if response.status_code == 200:
                print("   [OK] Associate dashboard accessible")
                
                # Check if travel requests are in context
                if hasattr(response, 'context') and response.context:
                    travel_requests = response.context.get('travel_requests', [])
                    print(f"   Travel requests in dashboard: {len(travel_requests)}")
                    
                    for req in travel_requests:
                        print(f"     - ID: {req.id}, User: {req.user.employee_id}, Status: {req.status}")
                else:
                    print("   ⚠️  No context data available")
            else:
                print(f"   ✗ Dashboard access failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Dashboard test error: {e}")
    
    # 4. Test Travel Request Details API
    print("\n4. Testing travel request details API...")
    
    if login_success:
        try:
            details_url = f'/auth/travel-request-details/{test_request.id}/'
            response = client.get(details_url)
            print(f"   Details API status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("   [OK] Travel request details accessible")
                    request_data = data.get('request', {})
                    print(f"     Employee: {request_data.get('employee_id')}")
                    print(f"     Status: {request_data.get('status')}")
                else:
                    print(f"   ✗ Details API error: {data.get('error')}")
            else:
                print(f"   ✗ Details API failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Details API test error: {e}")
    
    # 5. Test Travel Request Approval
    print("\n5. Testing travel request approval...")
    
    if login_success:
        try:
            approve_url = f'/auth/associate/approve-travel/{test_request.id}/'
            approval_data = {
                'action': 'approve',
                'remarks': 'Test approval from local system'
            }
            
            response = client.post(
                approve_url,
                data=json.dumps(approval_data),
                content_type='application/json'
            )
            
            print(f"   Approval API status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("   [OK] Travel request approval successful")
                    print(f"     Message: {data.get('message')}")
                    
                    # Verify status change
                    test_request.refresh_from_db()
                    print(f"     Updated status: {test_request.status}")
                    print(f"     Approved by: {test_request.approved_by.employee_id if test_request.approved_by else 'None'}")
                else:
                    print(f"   ✗ Approval failed: {data.get('error')}")
            else:
                print(f"   ✗ Approval API failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"     Error: {error_data}")
                except:
                    print(f"     Response content: {response.content}")
        except Exception as e:
            print(f"   ✗ Approval test error: {e}")
    
    # 6. Test URL Routing
    print("\n6. Testing URL routing...")
    
    test_urls = [
        ('associate_dashboard', []),
        ('travel_request_details', [test_request.id]),
        ('approve_travel_request', [test_request.id]),
    ]
    
    for url_name, args in test_urls:
        try:
            url = reverse(url_name, args=args)
            print(f"   [OK] {url_name}: {url}")
        except Exception as e:
            print(f"   ✗ {url_name}: {e}")
    
    # 7. Database Verification
    print("\n7. Database verification...")
    
    # Check Associate permissions
    print(f"   Associate permissions:")
    print(f"     - Can approve travel: {associate.can_approve_travel}")
    print(f"     - Role level: {associate.role_level}")
    print(f"     - DCCBs: {associate.multiple_dccb}")
    
    # Check travel request assignment
    print(f"   Travel request assignment:")
    print(f"     - Request user DCCB: {test_request.user.dccb}")
    print(f"     - Associate DCCBs: {associate.multiple_dccb}")
    print(f"     - DCCB match: {test_request.user.dccb in (associate.multiple_dccb or [])}")
    
    # Check queries that Associate dashboard uses
    user_dccbs = associate.multiple_dccb or []
    matching_requests = TravelRequest.objects.filter(
        user__dccb__in=user_dccbs
    )
    print(f"   Matching requests for Associate: {matching_requests.count()}")
    
    for req in matching_requests:
        print(f"     - ID: {req.id}, User: {req.user.employee_id} ({req.user.dccb}), Status: {req.status}")
    
    print("\n=== TEST SUMMARY ===")
    print(f"Associate User: {associate.employee_id} (password: test123)")
    print(f"Field User: {field_user.employee_id} (password: test123)")
    print(f"Test Request ID: {test_request.id}")
    print(f"Current Status: {test_request.status}")
    
    print("\nTo test manually:")
    print("1. Start local server: python manage.py runserver")
    print("2. Login as Associate: http://localhost:8000/auth/login/")
    print("3. Go to Associate Dashboard: http://localhost:8000/auth/associate-dashboard/")
    print("4. Try to approve the travel request")

if __name__ == '__main__':
    test_local_travel_system()