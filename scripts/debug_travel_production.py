#!/usr/bin/env python
"""
Production Travel Request Debug Script
Run this on production to diagnose travel request issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.db import connection

def debug_travel_requests():
    print("=== TRAVEL REQUEST PRODUCTION DEBUG ===\n")
    
    # 1. Check if TravelRequest table exists
    print("1. Checking TravelRequest table...")
    try:
        travel_count = TravelRequest.objects.count()
        print(f"   ✓ TravelRequest table exists with {travel_count} records")
    except Exception as e:
        print(f"   ✗ TravelRequest table error: {e}")
        return
    
    # 2. Check Associate users
    print("\n2. Checking Associate users...")
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    print(f"   Found {associates.count()} active Associates:")
    
    for assoc in associates:
        print(f"   - {assoc.employee_id}: {assoc.first_name} {assoc.last_name}")
        print(f"     DCCBs: {assoc.multiple_dccb}")
        print(f"     Can approve travel: {assoc.can_approve_travel}")
        print(f"     Role level: {assoc.role_level}")
    
    # 3. Check specific user MGJ00002
    print(f"\n3. Checking user MGJ00002...")
    try:
        user = CustomUser.objects.get(employee_id='MGJ00002')
        print(f"   ✓ User found: {user.first_name} {user.last_name}")
        print(f"   DCCB: {user.dccb}")
        print(f"   Designation: {user.designation}")
        print(f"   Role: {user.role}")
        print(f"   Role level: {user.role_level}")
        
        # Find Associate for this user's DCCB
        user_dccb = user.dccb
        matching_associates = []
        
        for assoc in associates:
            if assoc.multiple_dccb and user_dccb in assoc.multiple_dccb:
                matching_associates.append(assoc)
        
        if matching_associates:
            print(f"   ✓ Found {len(matching_associates)} Associates for DCCB '{user_dccb}':")
            for assoc in matching_associates:
                print(f"     - {assoc.employee_id}: {assoc.first_name} {assoc.last_name}")
        else:
            print(f"   ✗ No Associates found for DCCB '{user_dccb}'")
            print("   This is likely the root cause!")
            
    except CustomUser.DoesNotExist:
        print("   ✗ User MGJ00002 not found")
    
    # 4. Check travel requests for MGJ00002
    print(f"\n4. Checking travel requests for MGJ00002...")
    try:
        user_travel_requests = TravelRequest.objects.filter(user__employee_id='MGJ00002')
        print(f"   Found {user_travel_requests.count()} travel requests")
        
        for tr in user_travel_requests[:5]:  # Show last 5
            print(f"   - ID: {tr.id}, Status: {tr.status}, Created: {tr.created_at}")
            print(f"     Request to: {tr.request_to.employee_id if tr.request_to else 'None'}")
            
    except Exception as e:
        print(f"   Error checking travel requests: {e}")
    
    # 5. Check database tables
    print(f"\n5. Checking database tables...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%travel%';")
        tables = cursor.fetchall()
        print(f"   Travel-related tables: {[t[0] for t in tables]}")
    
    # 6. Check URL patterns (basic check)
    print(f"\n6. Checking URL configuration...")
    try:
        from django.urls import reverse
        urls_to_check = [
            'associate_dashboard',
            'travel_request_details',
            'approve_travel_request',
            'associate_travel_approvals'
        ]
        
        for url_name in urls_to_check:
            try:
                if url_name == 'travel_request_details':
                    url = reverse(url_name, args=[1])
                elif url_name == 'approve_travel_request':
                    url = reverse(url_name, args=[1])
                else:
                    url = reverse(url_name)
                print(f"   ✓ {url_name}: {url}")
            except Exception as e:
                print(f"   ✗ {url_name}: {e}")
                
    except Exception as e:
        print(f"   Error checking URLs: {e}")

if __name__ == '__main__':
    debug_travel_requests()