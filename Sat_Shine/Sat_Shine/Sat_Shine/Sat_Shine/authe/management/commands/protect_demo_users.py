from django.core.management.base import BaseCommand
from authe.models import CustomUser

class Command(BaseCommand):
    help = 'Mark existing MGJ00001-MGJ00005 users as protected demo users'

    def handle(self, *args, **options):
        demo_ids = ['MGJ00001', 'MGJ00002', 'MGJ00003', 'MGJ00004', 'MGJ00005']
        
        protected_count = 0
        not_found = []
        
        for employee_id in demo_ids:
            try:
                user = CustomUser.objects.get(employee_id=employee_id)
                user.is_demo_user = True
                user.save()
                protected_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Protected existing user: {employee_id} - {user.first_name} {user.last_name}')
                )
            except CustomUser.DoesNotExist:
                not_found.append(employee_id)
                self.stdout.write(
                    self.style.WARNING(f'User not found: {employee_id}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Summary: {protected_count} users protected from deletion')
        )
        
        if not_found:
            self.stdout.write(
                self.style.WARNING(f'Not found: {", ".join(not_found)}')
            )