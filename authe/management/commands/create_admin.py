from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Create default admin user for production'

    def handle(self, *args, **options):
        # Default admin credentials
        employee_id = 'MP0001'
        email = 'admin@satshine.com'
        password = 'SatShine@2024'
        
        # Check if admin already exists
        if CustomUser.objects.filter(employee_id=employee_id).exists():
            admin_user = CustomUser.objects.get(employee_id=employee_id)
            self.stdout.write(
                self.style.SUCCESS(f'Admin user {employee_id} already exists')
            )
            self.stdout.write(f'Employee ID: {admin_user.employee_id}')
            self.stdout.write(f'Email: {admin_user.email}')
            self.stdout.write(f'Name: {admin_user.get_full_name()}')
            self.stdout.write(f'Role: {admin_user.role}')
            return
        
        # Create admin user
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
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user: {employee_id}')
        )
        self.stdout.write(f'Employee ID: {employee_id}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Email: {email}')
        
        # Also create some test users
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
        
        for user_data in test_users:
            if not CustomUser.objects.filter(employee_id=user_data['employee_id']).exists():
                CustomUser.objects.create_user(**user_data)
                self.stdout.write(f'Created test user: {user_data["employee_id"]}')