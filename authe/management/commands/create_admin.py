from django.core.management.base import BaseCommand
from authe.models import CustomUser
from django.db import transaction

class Command(BaseCommand):
    help = 'Create superuser for production - SAFE for existing data'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Only create if no admin users exist at all
            admin_exists = CustomUser.objects.filter(
                role='admin'
            ).exists()
            
            if not admin_exists:
                user = CustomUser.objects.create_superuser(
                    username='MP0001',
                    employee_id='MP0001',
                    email='admin@satshine.com',
                    password='Admin@123',
                    first_name='ADMIN',
                    last_name='USER',
                    contact_number='9999999999',
                    designation='Manager'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Superuser created: {user.employee_id}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Admin user already exists - preserving existing data')
                )