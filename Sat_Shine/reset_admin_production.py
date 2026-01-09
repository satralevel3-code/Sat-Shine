#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

try:
    # Get or create admin user
    admin_user, created = CustomUser.objects.get_or_create(
        employee_id='MP0001',
        defaults={
            'username': 'MP0001',
            'email': 'admin@satshine.com',
            'first_name': 'ADMIN',
            'last_name': 'USER',
            'contact_number': '9999999999',
            'designation': 'Manager',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    # Set password
    admin_user.set_password('Admin@123')
    admin_user.is_active = True
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    
    print(f"✅ Admin user {'created' if created else 'updated'} successfully!")
    print(f"Employee ID: {admin_user.employee_id}")
    print(f"Password: Admin@123")
    print(f"Active: {admin_user.is_active}")
    print(f"Staff: {admin_user.is_staff}")
    print(f"Superuser: {admin_user.is_superuser}")
    
    # Test password
    if admin_user.check_password('Admin@123'):
        print("✅ Password verification successful!")
    else:
        print("❌ Password verification failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")