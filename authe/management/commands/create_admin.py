from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Create superuser for production'

    def handle(self, *args, **options):
        if not CustomUser.objects.filter(employee_id='MP0001').exists():
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
                self.style.WARNING('Superuser MP0001 already exists')
            )