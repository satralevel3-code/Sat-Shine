from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Create Django admin superuser'

    def handle(self, *args, **options):
        # Check if superuser already exists
        if CustomUser.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Superuser already exists')
            )
            return
        
        # Create superuser
        superuser = CustomUser.objects.create(
            employee_id='ADMIN001',
            username='ADMIN001',
            first_name='ADMIN',
            last_name='USER',
            email='admin@satshine.com',
            contact_number='9999999999',
            role='admin',
            designation='Manager',
            password=make_password('admin123'),
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Superuser created: {superuser.employee_id}')
        )
        self.stdout.write(
            self.style.SUCCESS('Username: ADMIN001')
        )
        self.stdout.write(
            self.style.SUCCESS('Password: admin123')
        )