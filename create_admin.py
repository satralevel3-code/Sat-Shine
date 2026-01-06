#!/usr/bin/env python
"""
Create superuser for production deployment
"""
import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')
django.setup()

from authe.models import CustomUser

def create_superuser():
    try:
        # Check if admin user exists
        if CustomUser.objects.filter(employee_id='MP0001').exists():
            print("Admin user already exists - preserving existing data")
            return
        
        # Create admin user
        admin_user = CustomUser.objects.create_user(
            employee_id='MP0001',
            email='admin@satshine.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            contact_number='9999999999',
            dccb='AHMEDABAD',
            designation='Manager',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        print(f"[OK] Admin user created: {admin_user.employee_id}")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    create_superuser()