from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from authe.models import Attendance

class Command(BaseCommand):
    help = 'Auto-update attendance to Half Day for missed check-outs'

    def handle(self, *args, **options):
        today = timezone.localdate()
        current_time = timezone.localtime().time()
        
        # Only run after 6 PM (18:00)
        if current_time < time(18, 0):
            self.stdout.write('Auto-update only runs after 6 PM')
            return
        
        # Find attendance records that are checked in but not checked out
        missed_checkouts = Attendance.objects.filter(
            date=today,
            status__in=['present'],  # Only convert Present to Half Day
            check_out_time__isnull=True
        )
        
        updated_count = 0
        for attendance in missed_checkouts:
            attendance.status = 'half_day'
            attendance.check_out_time = time(18, 0)  # Set default check-out time
            if attendance.remarks:
                attendance.remarks += ' | Auto-updated to Half Day (missed check-out)'
            else:
                attendance.remarks = 'Auto-updated to Half Day (missed check-out)'
            attendance.save()
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} attendance records to Half Day'
            )
        )