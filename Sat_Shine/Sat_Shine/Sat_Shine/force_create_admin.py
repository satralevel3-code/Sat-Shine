#!/usr/bin/env python
"""
Force create admin user - Run this in Railway console
This will definitely create the admin user regardless of existing state
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

def force_create_admin():
    """Force create admin user, delete existing if necessary"""
    
    # Delete existing MP0001 if exists
    try:
        existing_user = CustomUser.objects.filter(employee_id='MP0001')
        if existing_user.exists():
            existing_user.delete()
            print("🗑️ Deleted existing MP0001 user")
    except Exception as e:
        print(f"⚠️ Error deleting existing user: {e}")
    
    # Create fresh admin user
    try:
        admin_user = CustomUser.objects.create_user(
            employee_id='MP0001',
            username='MP0001',  # Explicitly set username
            email='admin@satshine.com',
            password='SatShine@2024',
            first_name='ADMIN',
            last_name='USER',
            contact_number='9999999999',
            designation='Manager',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        
        print("✅ Successfully created fresh MP0001 admin user!")
        print(f"👤 Employee ID: {admin_user.employee_id}")
        print(f"🔒 Password: SatShine@2024")
        print(f"📧 Email: {admin_user.email}")
        print(f"🔑 Role: {admin_user.role}")
        print(f"✅ Active: {admin_user.is_active}")
        print(f"👑 Superuser: {admin_user.is_superuser}")
        
        # Test authentication
        from django.contrib.auth import authenticate
        test_user = authenticate(username='MP0001', password='SatShine@2024')
        if test_user:
            print("✅ Authentication test: PASSED")
        else:
            print("❌ Authentication test: FAILED")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None

def create_test_users():
    """Create test users"""
    test_users = [
        {
            'employee_id': 'MGJ00001',
            'email': 'field1@satshine.com',
            'password': 'Field@2024',
            'first_name': 'FIELD',
            'last_name': 'OFFICER1',
            'contact_number': '9876543210',
            'designation': 'MT',
            'dccb': 'AHMEDABAD'
        }
    ]
    
    for user_data in test_users:
        try:
            # Delete existing if exists
            CustomUser.objects.filter(employee_id=user_data['employee_id']).delete()
            
            # Create fresh user
            CustomUser.objects.create_user(**user_data)
            print(f"✅ Created test user: {user_data['employee_id']}")
        except Exception as e:
            print(f"❌ Error creating {user_data['employee_id']}: {e}")

if __name__ == '__main__':
    print("🚀 Force Creating SAT-SHINE Admin User...")
    print("=" * 50)
    
    admin_user = force_create_admin()
    
    if admin_user:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! Admin user created.")
        print("🔗 Login URL: https://web-production-6396f.up.railway.app/auth/login/")
        print("👤 Employee ID: MP0001")
        print("🔒 Password: SatShine@2024")
        print("=" * 50)
        
        # Create test user
        create_test_users()
    else:
        print("\n❌ FAILED to create admin user. Check Railway logs for errors.")