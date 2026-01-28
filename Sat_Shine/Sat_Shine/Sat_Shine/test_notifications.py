#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\admin\\Git_demo\\Sat_shine')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Notification, Attendance, LeaveRequest, TravelRequest
from authe.notification_service import *
from django.utils import timezone
from datetime import date, time

def test_notification_system():
    print("=== TESTING NOTIFICATION SYSTEM ===\n")
    
    # Test 1: Check-in Reminder
    print("1. Testing Check-in Reminder...")
    try:
        send_check_in_reminder()
        reminder_count = Notification.objects.filter(
            notification_type='check_in_reminder',
            created_at__date=timezone.localdate()
        ).count()
        print(f"   SUCCESS Check-in reminders sent: {reminder_count}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Travel Request Notification
    print("\n2. Testing Travel Request Notification...")
    try:
        # Get a user and associate
        user = CustomUser.objects.filter(designation='MT', is_active=True).first()
        associate = CustomUser.objects.filter(designation='Associate', is_active=True).first()
        
        if user and associate:
            # Create a test travel request
            travel_request = TravelRequest.objects.create(
                user=user,
                from_date=timezone.localdate(),
                to_date=timezone.localdate(),
                duration='full_day',
                days_count=1.0,
                request_to=associate,
                er_id='TEST12345678901234',
                distance_km=50,
                address='Test address for notification testing purpose only',
                contact_person='9876543210',
                purpose='Testing notification system for travel request functionality'
            )
            
            notify_travel_request(travel_request)
            
            # Check if notification was created
            notif = Notification.objects.filter(
                recipient=associate,
                notification_type='travel_request'
            ).first()
            
            if notif:
                print(f"   SUCCESS Travel request notification sent to {associate.employee_id}")
                print(f"     Title: {notif.title}")
                print(f"     Message: {notif.message}")
            else:
                print("   ERROR Travel request notification not found")
                
            # Clean up
            travel_request.delete()
        else:
            print("   ERROR No MT user or Associate found for testing")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Attendance Marking Notification
    print("\n3. Testing Attendance Marking Notification...")
    try:
        user = CustomUser.objects.filter(designation='MT', is_active=True).first()
        if user:
            # Create test attendance
            attendance = Attendance.objects.create(
                user=user,
                date=timezone.localdate(),
                status='present',
                check_in_time=time(9, 15)
            )
            
            notify_attendance_marked(attendance)
            
            # Check DC notification
            dc_notif = Notification.objects.filter(
                recipient__designation='DC',
                recipient__dccb=user.dccb,
                notification_type='system_alert',
                title='Attendance Marked'
            ).first()
            
            # Check Admin notification
            admin_notif = Notification.objects.filter(
                recipient__role_level__gte=10,
                notification_type='system_alert',
                title='Daily Attendance Update'
            ).first()
            
            if dc_notif:
                print(f"   SUCCESS DC notification sent to {dc_notif.recipient.employee_id}")
            else:
                print("   ERROR DC notification not found")
                
            if admin_notif:
                print(f"   SUCCESS Admin notification sent to {admin_notif.recipient.employee_id}")
            else:
                print("   ERROR Admin notification not found")
                
            # Clean up
            attendance.delete()
        else:
            print("   ERROR No MT user found for testing")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Leave Request Notification
    print("\n4. Testing Leave Request Notification...")
    try:
        user = CustomUser.objects.filter(designation='MT', is_active=True).first()
        if user:
            # Create test leave request
            leave_request = LeaveRequest.objects.create(
                user=user,
                leave_type='planned',
                duration='full_day',
                start_date=timezone.localdate(),
                end_date=timezone.localdate(),
                days_requested=1.0,
                reason='Testing notification system'
            )
            
            notify_leave_request(leave_request)
            
            # Check admin notifications
            admin_notifs = Notification.objects.filter(
                recipient__role_level__gte=10,
                notification_type='leave_request'
            )
            
            if admin_notifs.exists():
                print(f"   SUCCESS Leave request notifications sent to {admin_notifs.count()} admins")
                for notif in admin_notifs[:2]:  # Show first 2
                    print(f"     -> {notif.recipient.employee_id}: {notif.title}")
            else:
                print("   ERROR Leave request notifications not found")
                
            # Clean up
            leave_request.delete()
        else:
            print("   ERROR No MT user found for testing")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 5: Check Notification Counts
    print("\n5. Current Notification Summary...")
    try:
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        
        print(f"   Total notifications in system: {total_notifications}")
        print(f"   Unread notifications: {unread_notifications}")
        
        # Show notifications by type
        notif_types = Notification.objects.values('notification_type').distinct()
        for notif_type in notif_types:
            count = Notification.objects.filter(notification_type=notif_type['notification_type']).count()
            print(f"   {notif_type['notification_type']}: {count}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 6: Check Users with Notifications
    print("\n6. Users with Notifications...")
    try:
        users_with_notifs = Notification.objects.values('recipient__employee_id').distinct()[:10]
        for user_notif in users_with_notifs:
            user_id = user_notif['recipient__employee_id']
            count = Notification.objects.filter(recipient__employee_id=user_id).count()
            unread = Notification.objects.filter(recipient__employee_id=user_id, is_read=False).count()
            print(f"   {user_id}: {count} total, {unread} unread")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== NOTIFICATION SYSTEM TEST COMPLETE ===")

if __name__ == '__main__':
    test_notification_system()