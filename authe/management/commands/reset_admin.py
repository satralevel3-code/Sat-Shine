from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Create or reset admin user'

    def handle(self, *args, **options):
        # Delete existing admin
        CustomUser.objects.filter(employee_id='MP0001').delete()
        
        # Create new admin
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
        
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Admin user created: {admin.employee_id}')
        )