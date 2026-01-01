from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AuditLog

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['employee_id', 'first_name', 'last_name', 'email', 'role', 'designation', 'is_active', 'date_joined']
    list_filter = ['role', 'designation', 'dccb', 'is_active', 'date_joined']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']
    ordering = ['employee_id']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'contact_number', 'role', 'designation', 'dccb', 'reporting_manager')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'contact_number', 
                      'role', 'designation', 'dccb', 'reporting_manager')
        }),
    )
    
    readonly_fields = ['role', 'date_joined', 'last_login']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__employee_id', 'user__first_name', 'user__last_name', 'action']
    readonly_fields = ['user', 'action', 'timestamp', 'ip_address', 'details']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False