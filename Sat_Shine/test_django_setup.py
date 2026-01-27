#!/usr/bin/env python
"""
Test Django setup and URL routing
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

def test_django_setup():
    print("=== Django Setup Test ===\n")
    
    try:
        # Test database connection
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connection: OK")
        
        # Test models
        from authe.models import CustomUser, TravelRequest
        user_count = CustomUser.objects.count()
        travel_count = TravelRequest.objects.count()
        print(f"✅ Models working: {user_count} users, {travel_count} travel requests")
        
        # Test MGJ00002 setup
        try:
            mgj00002 = CustomUser.objects.get(employee_id='MGJ00002')
            print(f"✅ MGJ00002 found: {mgj00002.first_name} {mgj00002.last_name}")
            print(f"   Designation: {mgj00002.designation}")
            print(f"   Can Approve Travel: {mgj00002.can_approve_travel}")
            print(f"   DCCBs: {mgj00002.multiple_dccb}")
        except CustomUser.DoesNotExist:
            print("❌ MGJ00002 not found")
        
        # Test URL imports
        try:
            from Sat_Shine.urls import urlpatterns
            print("✅ Main URL patterns loaded")
            
            from authe.urls import urlpatterns as authe_urls
            print("✅ Auth URL patterns loaded")
            
            from authe import views, admin_views, travel_views
            print("✅ All view modules imported successfully")
            
        except ImportError as e:
            print(f"❌ URL/View import error: {e}")
        
        # Test settings
        from django.conf import settings
        print(f"✅ DEBUG mode: {settings.DEBUG}")
        print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
        print(f"✅ Allowed hosts: {settings.ALLOWED_HOSTS}")
        
        print("\n🎉 Django setup is working correctly!")
        print("\nTo start the server, run:")
        print("python manage.py runserver")
        print("\nThen access: http://127.0.0.1:8000/auth/login/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_django_setup()