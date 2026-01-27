from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Fix user MGJ00002 configuration'

    def handle(self, *args, **options):
        try:
            user = CustomUser.objects.get(employee_id='MGJ00002')
            
            # Ensure user has DCCB
            if not user.dccb:
                user.dccb = 'AHMEDABAD'
                self.stdout.write(f'Assigned DCCB AHMEDABAD to {user.employee_id}')
            
            # Ensure proper designation
            if user.designation not in ['MT', 'DC', 'Support']:
                user.designation = 'MT'
                self.stdout.write(f'Set designation to MT for {user.employee_id}')
            
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated user: {user.employee_id}')
            )
            
        except CustomUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('User MGJ00002 not found')
            )