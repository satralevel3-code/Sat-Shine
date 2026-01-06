#!/usr/bin/env python
"""
Create superuser for production deployment with proper password hashing
"""
import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings_production')
django.setup()

from authe.models import CustomUser
from django.contrib.auth.hashers import make_password

def create_superuser():
    try:
        # Check if admin user exists
        if CustomUser.objects.filter(employee_id='MP0001').exists():
            print("Admin user already exists - preserving existing data")
            # Update password to ensure it's properly hashed
            admin_user = CustomUser.objects.get(employee_id='MP0001')
            admin_user.set_password('admin123')
            admin_user.save()
            print("[OK] Admin password updated and properly hashed")
            return
        
        # Create admin user with properly hashed password
        admin_user = CustomUser.objects.create(
            employee_id='MP0001',
            username='MP0001',
            email='admin@satshine.com',
            first_name='Admin',
            last_name='User',
            contact_number='9999999999',
            dccb='AHMEDABAD',
            designation='Manager',
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        admin_user.set_password('admin123')  # This properly hashes the password
        admin_user.save()
        print(f"[OK] Admin user created: {admin_user.employee_id}")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    create_superuser()