#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from django.utils import timezone
from datetime import timedelta, date

def test_date_range_issue():
    print("=" * 80)
    print("TESTING DATE RANGE ISSUE")
    print("=" * 80)
    
    # Get all travel requests
    all_requests = TravelRequest.objects.all().order_by('from_date')
    print(f"Total travel requests: {all_requests.count()}")
    
    if all_requests.exists():
        print("\nAll travel requests with dates:")
        for tr in all_requests:
            print(f"  - ID: {tr.id}, User: {tr.user.employee_id}")
            print(f"    From: {tr.from_date} To: {tr.to_date}")
            print(f"    Status: {tr.status}")
        
        # Check current default date range
        today = timezone.localdate()
        default_from = today
        default_to = today + timedelta(days=30)
        
        print(f"\nCurrent default date range:")
        print(f"  From: {default_from}")
        print(f"  To: {default_to}")
        
        # Check which requests fall in default range
        in_range = all_requests.filter(from_date__range=[default_from, default_to])
        print(f"\nRequests in default range: {in_range.count()}")
        
        # Check with wider range (last 30 days to next 60 days)
        wide_from = today - timedelta(days=30)
        wide_to = today + timedelta(days=60)
        
        print(f"\nWider date range:")
        print(f"  From: {wide_from}")
        print(f"  To: {wide_to}")
        
        in_wide_range = all_requests.filter(from_date__range=[wide_from, wide_to])
        print(f"Requests in wider range: {in_wide_range.count()}")
        
        if in_wide_range.exists():
            print("Requests in wider range:")
            for tr in in_wide_range:
                print(f"  - {tr.user.employee_id}: {tr.from_date} to {tr.to_date} ({tr.status})")
    
    print("\n" + "=" * 80)
    print("SOLUTION: Update Associate dashboard default date range")
    print("=" * 80)

if __name__ == "__main__":
    test_date_range_issue()