import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

# Delete existing superuser if exists
CustomUser.objects.filter(employee_id='MP0001').delete()

# Create new superuser with default password
superuser = CustomUser.objects.create_superuser(
    username='MP0001',
    employee_id='MP0001',
    email='admin@satshine.com',
    password='Admin@123',
    first_name='SAURAV',
    last_name='ADMIN',
    contact_number='9999999999',
    designation='Manager'
)
print(f"Superuser created successfully!")
print(f"Employee ID: {superuser.employee_id}")
print(f"Password: Admin@123")
print(f"Admin URL: http://127.0.0.1:8000/admin/")