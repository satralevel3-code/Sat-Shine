from django.core.management.base import BaseCommand
from authe.notification_service import cleanup_expired_notifications

class Command(BaseCommand):
    help = 'Clean up expired notifications'
    
    def handle(self, *args, **options):
        expired_count = cleanup_expired_notifications()
        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up {expired_count} expired notifications')
        )