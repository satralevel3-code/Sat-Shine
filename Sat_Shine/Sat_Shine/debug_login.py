#!/usr/bin/env python
"""
Debug script to diagnose login issues in production
Run this in Railway console: python debug_login.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser
from django.contrib.auth import authenticate
from django.db import connection

def check_database_connection():
    """Check if database is accessible"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_users_table():
    """Check if users exist in database"""
    try:
        total_users = CustomUser.objects.count()
        admin_users = CustomUser.objects.filter(role='admin').count()
        mp_users = CustomUser.objects.filter(employee_id__startswith='MP').count()
        
        print(f"📊 Total users in database: {total_users}")
        print(f"👤 Admin users: {admin_users}")
        print(f"🏢 MP users: {mp_users}")
        
        # List all users
        if total_users > 0:
            print("\n📋 All users in database:")
            for user in CustomUser.objects.all()[:10]:  # Limit to first 10
                print(f"   {user.employee_id} | {user.email} | {user.role} | Active: {user.is_active}")
        
        return total_users > 0
    except Exception as e:
        print(f"❌ Error checking users table: {e}")
        return False

def check_mp0001_user():
    """Check MP0001 user specifically"""
    try:
        user = CustomUser.objects.get(employee_id='MP0001')
        print(f"\n🔍 MP0001 User Details:")
        print(f"   Employee ID: {user.employee_id}")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   First Name: {user.first_name}")
        print(f"   Last Name: {user.last_name}")
        print(f"   Role: {user.role}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Is Staff: {user.is_staff}")
        print(f"   Is Superuser: {user.is_superuser}")
        print(f"   Has Usable Password: {user.has_usable_password()}")
        
        return user
    except CustomUser.DoesNotExist:
        print("❌ MP0001 user does not exist in database")
        return None
    except Exception as e:
        print(f"❌ Error checking MP0001 user: {e}")
        return None

def test_authentication():
    """Test authentication with MP0001"""
    try:
        # Test with employee_id as username
        user = authenticate(username='MP0001', password='SatShine@2024')
        if user:
            print("✅ Authentication successful with MP0001")
            return True
        else:
            print("❌ Authentication failed with MP0001")
            
            # Try different variations
            variations = [
                ('mp0001', 'SatShine@2024'),
                ('MP0001', 'satshine@2024'),
                ('MP0001', 'SatShine@2024'),
            ]
            
            for username, password in variations:
                user = authenticate(username=username, password=password)
                if user:
                    print(f"✅ Authentication successful with {username}/{password}")
                    return True
                else:
                    print(f"❌ Authentication failed with {username}/{password}")
            
            return False
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return False

def create_mp0001_user():
    """Create MP0001 user if it doesn't exist"""
    try:
        user, created = CustomUser.objects.get_or_create(
            employee_id='MP0001',
            defaults={
                'email': 'admin@satshine.com',
                'first_name': 'ADMIN',
                'last_name': 'USER',
                'contact_number': '9999999999',
                'designation': 'Manager',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password('SatShine@2024')
            user.save()
            print("✅ Created MP0001 user successfully")
        else:
            # Update password if user exists
            user.set_password('SatShine@2024')
            user.is_active = True
            user.save()
            print("✅ Updated MP0001 user password")
        
        return user
    except Exception as e:
        print(f"❌ Error creating MP0001 user: {e}")
        return None

def check_django_settings():
    """Check Django settings that might affect login"""
    from django.conf import settings
    
    print(f"\n⚙️ Django Settings:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SECRET_KEY: {'Set' if settings.SECRET_KEY else 'Not Set'}")
    print(f"   AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
    print(f"   TIME_ZONE: {settings.TIME_ZONE}")
    print(f"   USE_TZ: {settings.USE_TZ}")
    
    # Check database config
    db_config = settings.DATABASES['default']
    print(f"   Database Engine: {db_config['ENGINE']}")
    print(f"   Database Name: {db_config.get('NAME', 'Not Set')}")

def main():
    """Main debug function"""
    print("🔍 SAT-SHINE Production Login Debug")
    print("=" * 50)
    
    # Step 1: Check database connection
    if not check_database_connection():
        return
    
    # Step 2: Check Django settings
    check_django_settings()
    
    # Step 3: Check users table
    print("\n" + "=" * 50)
    if not check_users_table():
        print("⚠️ No users found in database. Creating MP0001...")
        create_mp0001_user()
    
    # Step 4: Check MP0001 user specifically
    print("\n" + "=" * 50)
    user = check_mp0001_user()
    
    if not user:
        print("⚠️ MP0001 user not found. Creating...")
        user = create_mp0001_user()
    
    # Step 5: Test authentication
    print("\n" + "=" * 50)
    print("🔐 Testing Authentication:")
    auth_success = test_authentication()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS SUMMARY:")
    print("=" * 50)
    
    if auth_success:
        print("✅ LOGIN SHOULD WORK NOW!")
        print("🔗 Login URL: https://web-production-6396f.up.railway.app/auth/login/")
        print("👤 Employee ID: MP0001")
        print("🔒 Password: SatShine@2024")
    else:
        print("❌ LOGIN ISSUE PERSISTS")
        print("🔧 Possible solutions:")
        print("   1. Run migrations: python manage.py migrate")
        print("   2. Check environment variables")
        print("   3. Check Railway logs for errors")
        print("   4. Verify database connectivity")

if __name__ == '__main__':
    main()