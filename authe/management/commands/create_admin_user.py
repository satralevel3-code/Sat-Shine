from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Create admin user for SAT-SHINE'

    def handle(self, *args, **options):
        if CustomUser.objects.filter(employee_id='MP0001').exists():
            self.stdout.write(
                self.style.WARNING('Admin user MP0001 already exists')
            )
            return

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

        self.stdout.write(
            self.style.SUCCESS('Successfully created admin user MP0001')
        )