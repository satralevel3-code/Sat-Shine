#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

# Create admin user if not exists
if not CustomUser.objects.filter(employee_id='MP0001').exists():
    admin_user = CustomUser(
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
        is_superuser=True
    )
    admin_user.set_password('admin123')
    admin_user.save()
    print("Admin user created: MP0001 / admin123")
else:
    print("Admin user already exists: MP0001")