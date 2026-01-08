import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

# Delete existing admin if exists
CustomUser.objects.filter(employee_id='MP0001').delete()

# Create admin user with only required fields
admin = CustomUser(
    username='MP0001',
    employee_id='MP0001',
    email='admin@satshine.com',
    first_name='ADMIN',
    last_name='USER',
    contact_number='9999999999',
    designation='Manager',
    role='admin',
    is_staff=True,
    is_superuser=True,
    is_active=True
)
admin.set_password('Admin@123')
admin.save()

print("Admin created successfully!")
print(f"Employee ID: {admin.employee_id}")
print(f"Password: Admin@123")
print(f"Active: {admin.is_active}")
print(f"Staff: {admin.is_staff}")
print(f"Superuser: {admin.is_superuser}")