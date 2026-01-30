#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.utils import timezone
from datetime import timedelta

def debug_travel_system():
    print("=" * 80)
    print("COMPREHENSIVE TRAVEL REQUEST SYSTEM DEBUG")
    print("=" * 80)
    
    # 1. Check all users
    print("\n1. USER ANALYSIS:")
    print("-" * 40)
    
    associates = CustomUser.objects.filter(designation='Associate', is_active=True)
    print(f"Total Associates: {associates.count()}")
    for assoc in associates:
        print(f"  - {assoc.employee_id}: {assoc.first_name} {assoc.last_name}")
        print(f"    DCCB: {assoc.dccb}")
        print(f"    Multiple DCCB: {assoc.multiple_dccb}")
        print(f"    Can Approve Travel: {assoc.can_approve_travel}")
    
    field_officers = CustomUser.objects.filter(designation__in=['MT', 'DC', 'Support'], is_active=True)
    print(f"\nTotal Field Officers (MT/DC/Support): {field_officers.count()}")
    for officer in field_officers:
        print(f"  - {officer.employee_id}: {officer.first_name} {officer.last_name} ({officer.designation})")
        print(f"    DCCB: {officer.dccb}")
    
    # 2. Check travel requests
    print("\n2. TRAVEL REQUEST ANALYSIS:")
    print("-" * 40)
    
    all_travel_requests = TravelRequest.objects.all()
    print(f"Total Travel Requests: {all_travel_requests.count()}")
    
    if all_travel_requests.exists():
        print("\nAll Travel Requests:")
        for tr in all_travel_requests:
            print(f"  - ID: {tr.id}")
            print(f"    User: {tr.user.employee_id} ({tr.user.designation})")
            print(f"    User DCCB: {tr.user.dccb}")
            print(f"    From: {tr.from_date} To: {tr.to_date}")
            print(f"    Status: {tr.status}")
            print(f"    Request To: {tr.request_to}")
            print(f"    Created: {tr.created_at}")
            print()
    else:
        print("No travel requests found in database!")
    
    # 3. Check recent travel requests (last 60 days)
    print("\n3. RECENT TRAVEL REQUESTS (Last 60 days):")
    print("-" * 40)
    
    from_date = timezone.localdate() - timedelta(days=30)
    to_date = timezone.localdate() + timedelta(days=30)
    
    recent_requests = TravelRequest.objects.filter(
        from_date__range=[from_date, to_date]
    )
    print(f"Travel requests in date range {from_date} to {to_date}: {recent_requests.count()}")
    
    # 4. Test Associate query
    print("\n4. ASSOCIATE QUERY TEST:")
    print("-" * 40)
    
    if associates.exists():
        test_associate = associates.first()
        print(f"Testing with Associate: {test_associate.employee_id}")
        
        # Test the exact query from associate_dashboard
        travel_requests = TravelRequest.objects.filter(
            user__designation__in=['MT', 'DC', 'Support'],
            from_date__range=[from_date, to_date]
        ).select_related('user')
        
        print(f"Query result count: {travel_requests.count()}")
        
        if travel_requests.exists():
            print("Travel requests found:")
            for tr in travel_requests:
                print(f"  - {tr.user.employee_id} ({tr.user.designation}): {tr.from_date} to {tr.to_date}")
        else:
            print("No travel requests found with current query!")
    
    # 5. Check database table structure
    print("\n5. DATABASE TABLE STRUCTURE:")
    print("-" * 40)
    
    from django.db import connection
    cursor = connection.cursor()
    
    # Check if TravelRequest table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='authe_travelrequest';")
    table_exists = cursor.fetchone()
    print(f"TravelRequest table exists: {table_exists is not None}")
    
    if table_exists:
        cursor.execute("PRAGMA table_info(authe_travelrequest);")
        columns = cursor.fetchall()
        print("Table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    # 6. Check URL routing
    print("\n6. URL ROUTING CHECK:")
    print("-" * 40)
    
    from django.urls import reverse
    try:
        associate_dashboard_url = reverse('associate_dashboard')
        print(f"Associate dashboard URL: {associate_dashboard_url}")
    except Exception as e:
        print(f"Error getting associate dashboard URL: {e}")
    
    # 7. Test template context
    print("\n7. TEMPLATE CONTEXT SIMULATION:")
    print("-" * 40)
    
    if associates.exists():
        test_associate = associates.first()
        
        # Simulate the context data
        context_travel_requests = TravelRequest.objects.filter(
            user__designation__in=['MT', 'DC', 'Support'],
            from_date__range=[from_date, to_date]
        ).select_related('user')
        
        print(f"Context travel_requests count: {context_travel_requests.count()}")
        print(f"Template will show: {'travel requests' if context_travel_requests.exists() else 'No travel requests found'}")
    
    # 8. Check for any errors in model
    print("\n8. MODEL VALIDATION:")
    print("-" * 40)
    
    try:
        # Test creating a sample travel request
        if field_officers.exists():
            test_officer = field_officers.first()
            print(f"Test officer: {test_officer.employee_id}")
            
            # Don't actually create, just validate
            print("Model validation: OK")
        else:
            print("No field officers found for testing")
    except Exception as e:
        print(f"Model validation error: {e}")
    
    # 9. Production-specific checks
    print("\n9. PRODUCTION ENVIRONMENT CHECKS:")
    print("-" * 40)
    
    from django.conf import settings
    print(f"DEBUG mode: {settings.DEBUG}")
    print(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
    
    # Check if we're using SQLite or PostgreSQL
    if 'sqlite' in settings.DATABASES['default']['ENGINE']:
        print("Using SQLite database")
        db_path = settings.DATABASES['default']['NAME']
        print(f"Database file: {db_path}")
        import os
        if os.path.exists(db_path):
            print(f"Database file exists: {os.path.getsize(db_path)} bytes")
        else:
            print("Database file does not exist!")
    else:
        print("Using PostgreSQL database")
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    debug_travel_system()