from django.core.management.base import BaseCommand
from django.utils import timezone
from authe.notification_service import send_check_in_reminder

class Command(BaseCommand):
    help = 'Send check-in reminder notifications at 9:00 AM'
    
    def handle(self, *args, **options):
        current_time = timezone.localtime()
        
        # Only send if it's 9:00 AM
        if current_time.hour == 9 and current_time.minute == 0:
            send_check_in_reminder()
            self.stdout.write(
                self.style.SUCCESS('Check-in reminders sent successfully')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Not 9:00 AM. Current time: {current_time.strftime("%H:%M")}')
            )