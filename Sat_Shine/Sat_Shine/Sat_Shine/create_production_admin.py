#!/usr/bin/env python
"""
Simple script to create admin user in production
Run this in Railway console: python create_production_admin.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

def create_admin_user():
    """Create default admin user for production"""
    
    # Admin credentials
    employee_id = 'MP0001'
    email = 'admin@satshine.com'
    password = 'SatShine@2024'
    
    # Check if admin exists
    if CustomUser.objects.filter(employee_id=employee_id).exists():
        admin_user = CustomUser.objects.get(employee_id=employee_id)
        print(f"✅ Admin user {employee_id} already exists")
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Name: {admin_user.get_full_name()}")
        print(f"🔑 Role: {admin_user.role}")
        print(f"🌐 Login URL: https://web-production-6396f.up.railway.app/auth/login/")
        return admin_user
    
    # Create admin user
    try:
        admin_user = CustomUser.objects.create_user(
            employee_id=employee_id,
            email=email,
            password=password,
            first_name='ADMIN',
            last_name='USER',
            contact_number='9999999999',
            designation='Manager',
            is_staff=True,
            is_superuser=True
        )
        
        print(f"🎉 Successfully created admin user!")
        print(f"👤 Employee ID: {employee_id}")
        print(f"🔒 Password: {password}")
        print(f"📧 Email: {email}")
        print(f"🌐 Login URL: https://web-production-6396f.up.railway.app/auth/login/")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None

def create_test_users():
    """Create test users for different roles"""
    
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
        },
        {
            'employee_id': 'MGJ00002',
            'email': 'dc1@satshine.com',
            'password': 'DC@2024',
            'first_name': 'DC',
            'last_name': 'USER1',
            'contact_number': '9876543211',
            'designation': 'DC',
            'dccb': 'BARODA'
        },
        {
            'employee_id': 'MGJ00080',
            'email': 'associate1@satshine.com',
            'password': 'Associate@2024',
            'first_name': 'ASSOCIATE',
            'last_name': 'USER1',
            'contact_number': '9876543212',
            'designation': 'Associate',
            'multiple_dccb': ['AHMEDABAD', 'BARODA', 'SURAT']
        }
    ]
    
    created_count = 0
    for user_data in test_users:
        if not CustomUser.objects.filter(employee_id=user_data['employee_id']).exists():
            try:
                CustomUser.objects.create_user(**user_data)
                print(f"✅ Created test user: {user_data['employee_id']}")
                created_count += 1
            except Exception as e:
                print(f"❌ Error creating {user_data['employee_id']}: {e}")
        else:
            print(f"ℹ️  Test user {user_data['employee_id']} already exists")
    
    return created_count

if __name__ == '__main__':
    print("🚀 Creating SAT-SHINE Production Users...")
    print("=" * 50)
    
    # Create admin user
    admin_user = create_admin_user()
    
    print("\n" + "=" * 50)
    print("👥 Creating test users...")
    
    # Create test users
    test_count = create_test_users()
    
    print("\n" + "=" * 50)
    print("📋 PRODUCTION LOGIN CREDENTIALS:")
    print("=" * 50)
    print("🔗 Login URL: https://web-production-6396f.up.railway.app/auth/login/")
    print("")
    print("👤 Admin Access:")
    print("   Employee ID: MP0001")
    print("   Password: SatShine@2024")
    print("")
    print("👥 Test Users:")
    print("   Field Officer: MGJ00001 / Field@2024")
    print("   DC User: MGJ00002 / DC@2024") 
    print("   Associate: MGJ00080 / Associate@2024")
    print("=" * 50)
    print("✅ Setup complete! You can now login to the system.")