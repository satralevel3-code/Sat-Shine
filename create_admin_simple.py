#!/usr/bin/env python
"""
Simple admin user creation script for Railway deployment
Run this in Railway console: python create_admin_simple.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

try:
    # Check if admin already exists
    if CustomUser.objects.filter(employee_id='MP0001').exists():
        print("❌ Admin user MP0001 already exists")
        admin = CustomUser.objects.get(employee_id='MP0001')
        print(f"   Employee ID: {admin.employee_id}")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   Active: {admin.is_active}")
    else:
        # Create new admin user
        admin = CustomUser(
            employee_id='MP0001',
            email='admin@satshine.com',
            first_name='ADMIN',
            last_name='USER',
            contact_number='9999999999',
            role='admin',
            designation='Manager',
            dccb='AHMEDABAD',
            is_active=True,
            is_staff=True,
            is_superuser=True,
            role_level=20  # Admin level
        )
        admin.set_password('admin123')
        admin.save()
        
        print("✅ Admin user created successfully!")
        print("   Employee ID: MP0001")
        print("   Password: admin123")
        print("   Email: admin@satshine.com")
        print("   Role: admin")
        
except Exception as e:
    print(f"❌ Error creating admin user: {e}")
    print("   Check if database is properly migrated")