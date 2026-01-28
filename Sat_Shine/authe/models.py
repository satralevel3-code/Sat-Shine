from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import time
import re
import uuid
import json

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('field_officer', 'Field Officer'),
        ('dc', 'DC'),
        ('mt', 'MT'),
        ('support', 'Support'),
        ('associate', 'Associate'),
        ('admin', 'Admin'),
        ('hr', 'HR'),
        ('manager', 'Manager'),
        ('delivery_head', 'Delivery Head'),
        ('super_admin', 'Super Admin'),
    ]
    
    DESIGNATION_CHOICES = [
        ('MT', 'MT'),
        ('DC', 'DC'),
        ('Support', 'Support'),
        ('Associate', 'Associate'),
        ('Manager', 'Manager'),
        ('HR', 'HR'),
        ('Delivery Head', 'Delivery Head'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('HR', 'HR'),
        ('SPMU', 'SPMU'),
        ('Central Tech Support', 'Central Tech Support'),
        ('CCR', 'CCR'),
        ('Field Support', 'Field Support'),
        ('IT Admin', 'IT Admin'),
    ]
    
    WORKPLACE_CHOICES = [
        ('DCCB', 'DCCB'),
        ('PACS', 'PACS'),
        ('WFH', 'WFH'),
        ('DR office', 'DR office'),
        ('DDM office', 'DDM office'),
        ('Training Centre', 'Training Centre'),
        ('Cluster', 'Cluster'),
        ('APMC', 'APMC'),
        ('Branch', 'Branch'),
        ('Vendor Office', 'Vendor Office'),
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
        validators=[RegexValidator(r'^(MGJ[0-9]{5}|MP[0-9]{4})$', 'Invalid Employee ID format')]
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    contact_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'Contact number must be 10 digits')]
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES)
    dccb = models.CharField(max_length=20, choices=DCCB_CHOICES, blank=True, null=True)
    reporting_manager = models.CharField(max_length=100, blank=True, null=True)
    
    # Enhanced enterprise fields
    role_level = models.IntegerField(default=1)
    can_approve_attendance = models.BooleanField(default=False)
    can_approve_travel = models.BooleanField(default=False)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    multiple_dccb = models.JSONField(default=list, blank=True)  # For Associates
    date_of_joining = models.DateField(null=True, blank=True)  # HR data, not auto timestamp
    
    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    def save(self, *args, **kwargs):
        # Auto-normalize Employee ID
        if self.employee_id:
            self.employee_id = self.employee_id.upper().strip()
            
        # Auto-assign role and level based on employee_id
        if self.employee_id.startswith('MGJ'):
            self.role = 'field_officer'
            self.role_level = 1
        elif self.employee_id.startswith('MP'):
            self.role = 'admin'
            self.role_level = 10
            self.can_approve_attendance = True
            
        # Set role level and permissions
        role_config = {
            'field_officer': {'level': 1, 'approve_attendance': False, 'approve_travel': False},
            'dc': {'level': 5, 'approve_attendance': True, 'approve_travel': False},
            'mt': {'level': 2, 'approve_attendance': False, 'approve_travel': False},
            'support': {'level': 2, 'approve_attendance': False, 'approve_travel': False},
            'associate': {'level': 7, 'approve_attendance': False, 'approve_travel': True},
            'admin': {'level': 10, 'approve_attendance': True, 'approve_travel': True},
            'hr': {'level': 10, 'approve_attendance': True, 'approve_travel': True},
            'manager': {'level': 10, 'approve_attendance': True, 'approve_travel': True},
            'delivery_head': {'level': 10, 'approve_attendance': True, 'approve_travel': True},
            'super_admin': {'level': 15, 'approve_attendance': True, 'approve_travel': True},
        }
        
        # Apply role-based configuration, but also check designation
        if self.role in role_config:
            config = role_config[self.role]
            self.role_level = config['level']
            self.can_approve_attendance = config['approve_attendance']
            self.can_approve_travel = config['approve_travel']
        
        # Override for Associates based on designation
        if self.designation == 'Associate':
            self.can_approve_travel = True
        
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
    
    TIME_STATUS_CHOICES = [
        ('on_time', 'On Time'),
        ('late', 'Late'),
        ('half_day_late', 'Half Day Late'),
    ]
    
    CONFIRMATION_SOURCE_CHOICES = [
        ('DC', 'DC'),
        ('ADMIN', 'Admin'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    
    # Enhanced attendance fields
    time_status = models.CharField(max_length=20, choices=TIME_STATUS_CHOICES, default='on_time')
    travel_required = models.BooleanField(default=False)
    travel_approved = models.BooleanField(default=False)
    workplace = models.CharField(max_length=50, choices=CustomUser.WORKPLACE_CHOICES, null=True, blank=True, default='DCCB')
    task = models.TextField(blank=True, null=True, default='')
    travel_reason = models.TextField(blank=True, null=True, default='')
    
    # GPS Location fields
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True)
    location_address = models.CharField(max_length=300, null=True, blank=True)
    is_location_valid = models.BooleanField(default=False)
    distance_from_office = models.FloatField(null=True, blank=True)
    
    # Approval workflow
    is_confirmed_by_dc = models.BooleanField(default=False)
    confirmed_by_dc = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='dc_confirmations')
    dc_confirmed_at = models.DateTimeField(null=True, blank=True)
    is_approved_by_admin = models.BooleanField(default=False)
    approved_by_admin = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='admin_approvals')
    admin_approved_at = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    confirmation_source = models.CharField(max_length=20, choices=CONFIRMATION_SOURCE_CHOICES, default='DC')
    is_leave_day = models.BooleanField(default=False)  # Mark if this absence is due to approved leave
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def save(self, *args, **kwargs):
        """Override save to enforce role-based DC confirmation rules"""
        # CRITICAL BUSINESS RULE: Associates and DCs NEVER need DC confirmation
        if self.user.designation in ['Associate', 'DC']:
            # Set to True so they skip DC pipeline entirely
            self.is_confirmed_by_dc = True
            self.confirmed_by_dc = None
            self.dc_confirmed_at = None
        
        super().save(*args, **kwargs)
    
    @property
    def timing_status(self):
        if self.check_in_time and self.check_in_time <= time(9, 30):
            return 'On Time'
        elif self.check_in_time:
            return 'Late Arrival'
        return 'Not Marked'
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.date} - {self.status}"

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
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='full_day')
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(null=True, blank=True)  # Admin comments on approval/rejection
    
    class Meta:
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.leave_type} - {self.start_date} to {self.end_date}"
    
    @property
    def days_count(self):
        return float(self.days_requested)

class AttendanceAuditLog(models.Model):
    """Audit log for attendance confirmation actions"""
    ACTION_TYPES = [
        ('DC_CONFIRMATION', 'DC Confirmation'),
        ('ADMIN_OVERRIDE', 'Admin Override'),
        ('BULK_UPDATE', 'Bulk Update'),
    ]
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    dc_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='audit_actions')
    affected_employee_count = models.IntegerField()
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action_type} by {self.dc_user.employee_id} - {self.timestamp}"

class TravelRequest(models.Model):
    """Enhanced travel request workflow"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    DURATION_CHOICES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='full_day')
    days_count = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    request_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='travel_requests_to_approve', null=True, blank=True)
    
    # Travel details
    er_id = models.CharField(max_length=17, validators=[RegexValidator(r'^[A-Z0-9]{17}$', 'ER ID must be 17 characters')])
    distance_km = models.IntegerField()
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    purpose = models.TextField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL, related_name='approved_travels')
    approved_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.from_date} to {self.to_date}"

class SystemAuditLog(models.Model):
    """Enterprise immutable audit logging"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actor = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    action_type = models.CharField(max_length=50)
    target_table = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    device_info = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_audit_logs'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['actor', 'action_type'])
        ]

class Notification(models.Model):
    """System notifications and alerts"""
    NOTIFICATION_TYPES = [
        ('check_in_reminder', 'Check-in Reminder'),
        ('travel_request', 'Travel Request'),
        ('travel_approval', 'Travel Approval'),
        ('leave_request', 'Leave Request'),
        ('leave_approval', 'Leave Approval'),
        ('system_alert', 'System Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Auto-expire notifications
    related_object_id = models.CharField(max_length=50, null=True, blank=True)  # For clearing related notifications
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.employee_id} - {self.title}"
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False