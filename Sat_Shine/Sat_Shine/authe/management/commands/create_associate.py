from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Create Associate user for travel approvals'

    def handle(self, *args, **options):
        # Check if Associate already exists
        if CustomUser.objects.filter(designation='Associate', is_active=True).exists():
            self.stdout.write(self.style.SUCCESS('Associate user already exists'))
            return

        # Create Associate user
        associate = CustomUser.objects.create_user(
            employee_id='MP0001',
            email='associate@satshine.com',
            password='Associate123!',
            first_name='SYSTEM',
            last_name='ASSOCIATE',
            designation='Associate',
            role='admin',
            contact_number='9999999999',
            multiple_dccb=['AHMEDABAD', 'BARODA', 'BHARUCH', 'KHEDA', 'PANCHMAHAL', 'SABARKANTHA', 'MAHESANA', 'BANASKANTHA']
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created Associate user: {associate.employee_id}')
        )