#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser
from datetime import date

def create_test_users():
    print("Creating test users...")
    
    # Create Associates
    associate1 = CustomUser.objects.create_user(
        employee_id='MGJ00001',
        first_name='JOHN',
        last_name='ASSOCIATE',
        email='john.associate@test.com',
        contact_number='9876543210',
        designation='Associate',
        dccb='AHMEDABAD',
        multiple_dccb=['AHMEDABAD', 'SURAT', 'RAJKOT'],
        can_approve_travel=True,
        role='field_officer',
        role_level=5,
        password='password123'
    )
    print(f"Created Associate: {associate1.employee_id}")
    
    # Create Field Officers
    field_officers = [
        {'id': 'MGJ00002', 'name': 'AMIT SHARMA', 'designation': 'MT', 'dccb': 'AHMEDABAD'},
        {'id': 'MGJ00003', 'name': 'PRIYA PATEL', 'designation': 'DC', 'dccb': 'SURAT'},
        {'id': 'MGJ00004', 'name': 'RAHUL SINGH', 'designation': 'Support', 'dccb': 'RAJKOT'},
        {'id': 'MGJ00005', 'name': 'SNEHA GUPTA', 'designation': 'MT', 'dccb': 'AHMEDABAD'},
    ]
    
    for officer in field_officers:
        user = CustomUser.objects.create_user(
            employee_id=officer['id'],
            first_name=officer['name'].split()[0],
            last_name=officer['name'].split()[1],
            email=f"{officer['name'].lower().replace(' ', '.')}@test.com",
            contact_number='9876543210',
            designation=officer['designation'],
            dccb=officer['dccb'],
            role='field_officer',
            role_level=1,
            password='password123'
        )
        print(f"Created {officer['designation']}: {user.employee_id} - {officer['name']}")
    
    print("\nTest users created successfully!")
    print("\nLogin credentials:")
    print("- Associate: MGJ00001 / password123")
    print("- Field Officers: MGJ00002, MGJ00003, MGJ00004, MGJ00005 / password123")
    print("- Admin: MP0001 / admin123")

if __name__ == "__main__":
    create_test_users()