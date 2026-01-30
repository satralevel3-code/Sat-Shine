#!/usr/bin/env python
"""
SAT-SHINE Admin User Setup Script
Run this on Railway console to create admin user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

print("🔍 SAT-SHINE Admin User Setup")
print("=" * 50)

# Check existing users
print("\n1. Checking existing users...")
all_users = CustomUser.objects.all()
print(f"   Total users in database: {all_users.count()}")

if all_users.count() > 0:
    print("\n   Existing users:")
    for user in all_users:
        print(f"   - {user.employee_id} | {user.email} | Role: {user.role} | Active: {user.is_active}")

# Check for existing admin
admin_exists = CustomUser.objects.filter(employee_id='MP0001').exists()
print(f"\n2. Admin user MP0001 exists: {admin_exists}")

if admin_exists:
    admin = CustomUser.objects.get(employee_id='MP0001')
    print(f"   Employee ID: {admin.employee_id}")
    print(f"   Email: {admin.email}")
    print(f"   Role: {admin.role}")
    print(f"   Role Level: {admin.role_level}")
    print(f"   Active: {admin.is_active}")
    print(f"   Staff: {admin.is_staff}")
    print(f"   Superuser: {admin.is_superuser}")
    
    # Reset password for existing admin
    print("\n3. Resetting admin password...")
    admin.set_password('admin123')
    admin.role = 'admin'
    admin.role_level = 20
    admin.is_active = True
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    print("   ✅ Admin password reset to 'admin123'")
    
else:
    print("\n3. Creating new admin user...")
    try:
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
            role_level=20
        )
        admin.set_password('admin123')
        admin.save()
        print("   ✅ Admin user created successfully!")
    except Exception as e:
        print(f"   ❌ Error creating admin: {e}")

print("\n" + "=" * 50)
print("🎯 ADMIN LOGIN CREDENTIALS:")
print("   Employee ID: MP0001")
print("   Password: admin123")
print("   Login URL: /login/")
print("=" * 50)

# Verify admin can be retrieved
try:
    final_admin = CustomUser.objects.get(employee_id='MP0001')
    print(f"\n✅ Verification: Admin user {final_admin.employee_id} is ready")
    print(f"   Role Level: {final_admin.role_level} (should be 20 for admin)")
    print(f"   Active: {final_admin.is_active}")
except CustomUser.DoesNotExist:
    print("\n❌ Verification failed: Admin user not found")