# Enterprise Permission System for MMP

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def check_enterprise_permission(user, action):
    """MMP Role-based permission system"""
    if not user.is_authenticated:
        return False
        
    # Action-based permission mapping for MMP
    action_permissions = {
        # Field Officer Actions
        'mark_attendance': ['field_officer', 'dc', 'mt', 'support', 'associate'],
        'apply_leave': ['field_officer', 'dc', 'mt', 'support', 'associate'],
        'request_travel': ['field_officer', 'dc', 'mt', 'support'],
        
        # DC Actions  
        'confirm_attendance': ['dc'],
        'view_team_attendance': ['dc', 'admin', 'hr', 'manager'],
        
        # Associate Actions
        'approve_travel': ['associate', 'admin', 'hr', 'manager'],
        
        # Admin Actions
        'manage_employees': ['admin', 'hr', 'manager', 'super_admin'],
        'approve_final_attendance': ['admin', 'hr', 'manager'],
        'bulk_operations': ['admin', 'hr', 'super_admin'],
        'export_reports': ['admin', 'hr', 'manager', 'delivery_head'],
        
        # Super Admin Actions
        'system_settings': ['super_admin'],
        'hard_delete': ['super_admin'],
        'modify_audit_logs': ['super_admin'],
    }
    
    required_roles = action_permissions.get(action, [])
    return user.role in required_roles

def check_hierarchy_permission(user, target_user, action):
    """Check if user can perform action on target_user based on hierarchy"""
    
    # Self operations always allowed
    if user == target_user:
        return True
        
    # Super Admin can do anything
    if user.role == 'super_admin':
        return True
        
    # Role level hierarchy check
    if user.role_level <= target_user.role_level:
        return False
        
    # Reporting hierarchy check
    if target_user.reporting_manager == user.employee_id:
        return True
        
    # DCCB-based permissions for admins
    if user.role in ['admin', 'hr', 'manager'] and user.dccb == target_user.dccb:
        return True
        
    return False

def log_enterprise_action(user, action_type, target_table, target_id, old_value=None, new_value=None, ip_address=None):
    """Enterprise audit logging for MMP"""
    from .models import SystemAuditLog
    
    try:
        SystemAuditLog.objects.create(
            actor=user,
            action_type=action_type,
            target_table=target_table,
            target_id=str(target_id),
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address or '127.0.0.1'
        )
    except Exception as e:
        # Never fail the main operation due to audit logging
        pass