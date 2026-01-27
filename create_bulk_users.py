#!/usr/bin/env python
import os
import sys
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser
from django.db import transaction

def create_users_from_csv():
    print("Creating users from CSV template...")
    
    # Sample user data
    users_data = [
        {
            'employee_id': 'MGJ00001',
            'first_name': 'JOHN',
            'last_name': 'DOE',
            'designation': 'MT',
            'department': 'Field Support',
            'contact_number': '9876543210',
            'dccb': 'AHMEDABAD',
            'reporting_manager': 'MANAGER NAME',
            'email': 'john.doe@test.com',
            'password': 'SecurePass123!'
        },
        {
            'employee_id': 'MGJ00002',
            'first_name': 'JANE',
            'last_name': 'SMITH',
            'designation': 'Associate',
            'department': 'Field Support',
            'contact_number': '9876543211',
            'multiple_dccb': ['AHMEDABAD', 'SURAT'],
            'reporting_manager': 'MANAGER NAME',
            'email': 'jane.smith@test.com',
            'password': 'SecurePass456@'
        },
        {
            'employee_id': 'MGJ00003',
            'first_name': 'AMIT',
            'last_name': 'PATEL',
            'designation': 'DC',
            'department': 'Field Support',
            'contact_number': '9876543212',
            'dccb': 'SURAT',
            'reporting_manager': 'MANAGER NAME',
            'email': 'amit.patel@test.com',
            'password': 'SecurePass789#'
        },
        {
            'employee_id': 'MGJ00004',
            'first_name': 'PRIYA',
            'last_name': 'SHARMA',
            'designation': 'Support',
            'department': 'Field Support',
            'contact_number': '9876543213',
            'dccb': 'RAJKOT',
            'reporting_manager': 'MANAGER NAME',
            'email': 'priya.sharma@test.com',
            'password': 'SecurePass101$'
        }
    ]
    
    created_count = 0
    
    try:
        with transaction.atomic():
            for user_data in users_data:
                # Check if user already exists
                if CustomUser.objects.filter(employee_id=user_data['employee_id']).exists():
                    print(f"User {user_data['employee_id']} already exists, skipping...")
                    continue
                
                # Create user
                user = CustomUser(
                    employee_id=user_data['employee_id'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    designation=user_data['designation'],
                    department=user_data['department'],
                    contact_number=user_data['contact_number'],
                    dccb=user_data.get('dccb'),
                    multiple_dccb=user_data.get('multiple_dccb', []),
                    reporting_manager=user_data.get('reporting_manager')
                )
                user.set_password(user_data['password'])
                user.save()
                
                print(f"Created user: {user.employee_id} - {user.first_name} {user.last_name} ({user.designation})")
                created_count += 1
        
        print(f"\nSuccessfully created {created_count} users!")
        
        # Show all users
        print("\nAll users in system:")
        all_users = CustomUser.objects.all().order_by('employee_id')
        for user in all_users:
            print(f"- {user.employee_id}: {user.first_name} {user.last_name} ({user.designation}) - {user.email}")
        
    except Exception as e:
        print(f"Error creating users: {e}")

if __name__ == "__main__":
    create_users_from_csv()