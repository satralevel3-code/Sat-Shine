#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser, Attendance, LeaveRequest
from django.contrib.auth import authenticate
from django.utils import timezone

print("=== SAT-SHINE SYSTEM TEST ===\n")

# 1. Test User Accounts
print("1. USER ACCOUNTS:")
total_users = CustomUser.objects.count()
field_officers = CustomUser.objects.filter(role='field_officer').count()
admins = CustomUser.objects.filter(role='admin').count()

print(f"   Total users: {total_users}")
print(f"   Field Officers: {field_officers}")
print(f"   Admins: {admins}")

# 2. Test Admin Login
print("\n2. ADMIN LOGIN TEST:")
admin = CustomUser.objects.filter(employee_id='MP0001').first()
if admin:
    print(f"   Admin exists: YES")
    print(f"   Password works: {'YES' if admin.check_password('Admin@123') else 'NO'}")
    print(f"   Is active: {'YES' if admin.is_active else 'NO'}")
    print(f"   Is staff: {'YES' if admin.is_staff else 'NO'}")
    print(f"   Is superuser: {'YES' if admin.is_superuser else 'NO'}")
    
    # Test authentication
    auth_test = authenticate(username='MP0001', password='Admin@123')
    print(f"   Authentication: {'YES' if auth_test else 'NO'}")
else:
    print("   Admin user: NO - NOT FOUND")

# 3. Test Field Officer Accounts
print("\n3. FIELD OFFICER ACCOUNTS:")
field_officers_list = CustomUser.objects.filter(role='field_officer')[:3]
for fo in field_officers_list:
    print(f"   {fo.employee_id} - {fo.first_name} {fo.last_name} ({fo.designation}) - {'Active' if fo.is_active else 'Inactive'}")

# 4. Test Database Tables
print("\n4. DATABASE TABLES:")
attendance_count = Attendance.objects.count()
leave_count = LeaveRequest.objects.count()
print(f"   Attendance records: {attendance_count}")
print(f"   Leave requests: {leave_count}")

# 5. Test URL Patterns
print("\n5. URL PATTERN TEST:")
from django.urls import reverse
try:
    login_url = reverse('login')
    register_url = reverse('register')
    admin_dashboard_url = reverse('admin_dashboard')
    field_dashboard_url = reverse('field_dashboard')
    mark_attendance_url = reverse('mark_attendance')
    
    print(f"   Login URL: YES {login_url}")
    print(f"   Register URL: YES {register_url}")
    print(f"   Admin Dashboard URL: YES {admin_dashboard_url}")
    print(f"   Field Dashboard URL: YES {field_dashboard_url}")
    print(f"   Mark Attendance URL: YES {mark_attendance_url}")
except Exception as e:
    print(f"   URL Error: NO {e}")

# 6. Test Model Relationships
print("\n6. MODEL RELATIONSHIPS:")
try:
    # Test if we can create relationships
    if field_officers_list:
        fo = field_officers_list[0]
        attendance_for_user = Attendance.objects.filter(user=fo).count()
        leaves_for_user = LeaveRequest.objects.filter(user=fo).count()
        print(f"   User-Attendance relationship: YES ({attendance_for_user} records)")
        print(f"   User-Leave relationship: YES ({leaves_for_user} records)")
    else:
        print("   No field officers to test relationships")
except Exception as e:
    print(f"   Relationship Error: NO {e}")

print("\n=== TEST COMPLETE ===")
print("Local server should be accessible at: http://127.0.0.1:8001/")
print("Try these URLs:")
print("- Registration: http://127.0.0.1:8001/auth/register/")
print("- Login: http://127.0.0.1:8001/auth/login/")
print("- Admin Dashboard: http://127.0.0.1:8001/auth/admin-dashboard/")