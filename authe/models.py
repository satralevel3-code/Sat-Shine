from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import RegexValidator
from django.utils import timezone
import re
import os

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('field_officer', 'Field Officer'),
        ('admin', 'Admin'),
    ]
    
    DESIGNATION_CHOICES = [
        ('MT', 'MT'),
        ('DC', 'DC'),
        ('Support', 'Support'),
        ('Manager', 'Manager'),
        ('HR', 'HR'),
        ('Delivery Head', 'Delivery Head'),
    ]
    
    DCCB_CHOICES = [
        ('AHMEDABAD', 'AHMEDABAD'),
        ('BANASKANTHA', 'BANASKANTHA'),
        ('BARODA', 'BARODA'),
        ('MAHESANA', 'MAHESANA'),
        ('SABARKANTHA', 'SABARKANTHA'),
        ('BHARUCH', 'BHARUCH'),
        ('KHEDA', 'KHEDA'),
        ('PANCHMAHAL', 'PANCHMAHAL'),
        ('SURENDRANAGAR', 'SURENDRANAGAR'),
        ('JAMNAGAR', 'JAMNAGAR'),
        ('JUNAGADH', 'JUNAGADH'),
        ('KODINAR', 'KODINAR'),
        ('KUTCH', 'KUTCH'),
        ('VALSAD', 'VALSAD'),
        ('AMRELI', 'AMRELI'),
        ('BHAVNAGAR', 'BHAVNAGAR'),
        ('RAJKOT', 'RAJKOT'),
        ('SURAT', 'SURAT'),
    ]
    
    employee_id = models.CharField(
        max_length=8, 
        unique=True,
        validators=[RegexValidator(r'^(MGJ[0-9]{5}|MP[0-9]{4})$', 'Invalid Employee ID format')],
        db_index=True
    )
    first_name = models.CharField(max_length=50, db_index=True)
    last_name = models.CharField(max_length=50, db_index=True)
    contact_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'Contact number must be 10 digits')]
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, db_index=True)
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES, db_index=True)
    dccb = models.CharField(max_length=20, choices=DCCB_CHOICES, blank=True, null=True, db_index=True)
    reporting_manager = models.CharField(max_length=100, blank=True, null=True)
    
    # GIS Fields for office location
    office_location = gis_models.PointField(srid=4326, null=True, blank=True, help_text="Office location coordinates")
    
    office_address = models.CharField(max_length=300, blank=True, null=True)
    attendance_radius = models.FloatField(default=500.0, help_text="Allowed attendance radius in meters")
    is_demo_user = models.BooleanField(default=False, help_text="Protected demo user - cannot be deleted")
    
    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['dccb', 'designation']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-normalize Employee ID
        if self.employee_id:
            self.employee_id = self.employee_id.upper().strip()
            
        # Auto-assign role based on employee_id
        if self.employee_id.startswith('MGJ'):
            self.role = 'field_officer'
        elif self.employee_id.startswith('MP'):
            self.role = 'admin'
        
        # Convert names and reporting manager to uppercase
        if self.first_name:
            self.first_name = self.first_name.upper()
        if self.last_name:
            self.last_name = self.last_name.upper()
        if self.reporting_manager:
            self.reporting_manager = self.reporting_manager.upper()
        
        # Set username to employee_id
        self.username = self.employee_id
        
        super().save(*args, **kwargs)
    
    def set_office_location(self, latitude, longitude):
        """Set office location from coordinates"""
        self.office_location = Point(longitude, latitude, srid=4326)
    
    def is_within_attendance_radius(self, latitude, longitude):
        """Check if given coordinates are within attendance radius"""
        if not self.office_location:
            return True  # Allow if no office location set
        
        user_point = Point(longitude, latitude, srid=4326)
        distance = self.office_location.distance(user_point) * 111000  # Convert to meters
        return distance <= self.attendance_radius
    
    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

class AuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.action} - {self.timestamp}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('half_day', 'Half Day'),
        ('absent', 'Absent'),
        ('auto_not_marked', 'Auto Not Marked'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_index=True)
    date = models.DateField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    
    # GIS location fields
    check_in_location = gis_models.PointField(srid=4326, null=True, blank=True)
    check_out_location = gis_models.PointField(srid=4326, null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    location_address = models.CharField(max_length=300, null=True, blank=True)
    is_location_valid = models.BooleanField(default=True)
    distance_from_office = models.FloatField(null=True, blank=True, help_text="Distance in meters")
    
    remarks = models.TextField(null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'user']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['marked_at']),
        ]
    
    def set_check_in_location(self, latitude, longitude):
        """Set check-in location and validate distance"""
        self.check_in_location = Point(longitude, latitude, srid=4326)
        if self.user.office_location:
            distance = self.user.office_location.distance(self.check_in_location) * 111000
            self.distance_from_office = distance
            self.is_location_valid = distance <= self.user.attendance_radius
    
    def set_check_out_location(self, latitude, longitude):
        """Set check-out location"""
        self.check_out_location = Point(longitude, latitude, srid=4326)
    
    @property
    def is_late(self):
        """Check attendance timing status based on new rules"""
        if not self.check_in_time:
            return False
        
        from datetime import time
        on_time_cutoff = time(10, 0)      # 10:00 AM
        late_cutoff = time(13, 30)        # 1:30 PM
        
        if self.check_in_time <= on_time_cutoff:
            return False  # On time
        elif self.check_in_time <= late_cutoff:
            return True   # Late arrival
        else:
            return False  # Half day (not considered "late")
    
    @property
    def timing_status(self):
        """Get timing status based on check-in time"""
        if not self.check_in_time:
            return 'Not Marked'
        
        from datetime import time
        on_time_cutoff = time(10, 0)      # 10:00 AM
        late_cutoff = time(13, 30)        # 1:30 PM
        half_day_cutoff = time(15, 0)     # 3:00 PM
        
        if self.check_in_time <= on_time_cutoff:
            return 'On Time'
        elif self.check_in_time <= late_cutoff:
            return 'Late Arrival'
        elif self.check_in_time <= half_day_cutoff:
            return 'Half Day Entry'
        else:
            return 'Very Late'
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.date} - {self.status}"

class Holiday(models.Model):
    date = models.DateField(unique=True, db_index=True)
    name = models.CharField(max_length=100)
    dccb = models.CharField(max_length=20, choices=CustomUser.DCCB_CHOICES, blank=True, null=True, db_index=True)
    is_national = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        ordering = ['date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['dccb', 'date']),
        ]
    
    def __str__(self):
        return f"{self.date} - {self.name}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    LEAVE_TYPES = [
        ('planned', 'Planned'),
        ('unplanned', 'Unplanned'),
    ]
    
    DURATION_CHOICES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_index=True)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, db_index=True)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='full_day')
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    days_requested = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'applied_at']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.leave_type} - {self.start_date} to {self.end_date}"
    
    @property
    def days_count(self):
        return float(self.days_requested)