#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, TravelRequest
from datetime import date, timedelta

def create_travel_requests():
    print("Creating travel requests...")
    
    # Get field officers
    users = CustomUser.objects.filter(designation__in=['MT', 'DC', 'Support'])
    
    for i, user in enumerate(users):
        tr = TravelRequest.objects.create(
            user=user,
            from_date=date.today() + timedelta(days=i),
            to_date=date.today() + timedelta(days=i),
            duration='full_day',
            days_count=1,
            er_id=f'ER{str(i+1).zfill(17)}',
            distance_km=25 + (i * 10),
            address=f'Test Address {i+1} for Travel Request Testing Purpose Location',
            contact_person=f'98765432{i:02d}',
            purpose=f'Travel request {i+1} for testing Associate dashboard approval system',
            status='pending'
        )
        print(f'Created travel request for {user.employee_id}')
    
    print('Travel requests created successfully!')
    
    # Show all travel requests
    all_requests = TravelRequest.objects.all()
    print(f"\nTotal travel requests: {all_requests.count()}")
    for tr in all_requests:
        print(f"- {tr.user.employee_id}: {tr.from_date} to {tr.to_date} ({tr.status})")

if __name__ == "__main__":
    create_travel_requests()