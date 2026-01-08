import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

# Delete existing admin if exists
CustomUser.objects.filter(employee_id='MP0001').delete()

# Create admin user
admin = CustomUser.objects.create_user(
    username='MP0001',
    employee_id='MP0001',
    email='admin@satshine.com',
    password='Admin@123',
    first_name='ADMIN',
    last_name='USER',
    contact_number='9999999999',
    designation='Manager',
    role='admin'
)

# Set admin permissions
admin.is_staff = True
admin.is_superuser = True
admin.is_active = True
admin.save()

print("Admin created successfully!")
print(f"Employee ID: {admin.employee_id}")
print(f"Password: Admin@123")
print(f"Active: {admin.is_active}")
print(f"Staff: {admin.is_staff}")
print(f"Superuser: {admin.is_superuser}")