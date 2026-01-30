"""
Travel Approval Dependency Validator
Enforces business rule: DC cannot confirm MT/Support attendance without approved travel
"""

from .models import TravelRequest, Attendance, CustomUser
from django.utils import timezone

def validate_travel_approval_for_dc_confirmation(attendance):
    """
    Validates if DC can confirm attendance based on travel approval status.
    
    Business Rule:
    - Applies ONLY to MT and Support designations
    - Applies ONLY to Present and Half Day status
    - Blocks DC confirmation if travel request is PENDING (Associate hasn't acted)
    - Allows DC confirmation if Associate has taken action (approved OR rejected)
    - Allows DC confirmation if NO travel request exists
    
    Returns:
        tuple: (can_confirm: bool, error_message: str or None)
    """
    
    # Rule does NOT apply to Associates and DCs
    if attendance.user.designation in ['Associate', 'DC']:
        return (True, None)
    
    # Rule applies ONLY to MT and Support
    if attendance.user.designation not in ['MT', 'Support']:
        return (True, None)
    
    # Rule applies ONLY to Present and Half Day
    if attendance.status not in ['present', 'half_day']:
        return (True, None)
    
    # Check if travel request exists for this date
    travel_requests = TravelRequest.objects.filter(
        user=attendance.user,
        from_date__lte=attendance.date,
        to_date__gte=attendance.date
    )
    
    # If no travel request exists, DC confirmation allowed
    if not travel_requests.exists():
        return (True, None)
    
    # Handle multiple travel requests (invalid state)
    if travel_requests.count() > 1:
        return (False, "Multiple travel requests found for this date. Please contact Admin.")
    
    # Get the travel request for this date
    travel_request = travel_requests.first()
    
    # Check travel approval status
    if travel_request.status == 'pending':
        # Travel pending - Block DC confirmation until Associate takes action
        return (False, "Travel Request is pending")
    
    # Associate has taken action (approved OR rejected) - DC can confirm
    return (True, None)


def validate_dc_attendance_for_admin_approval(attendance):
    """
    Validates if Admin can approve DC attendance based on travel approval status.
    
    Business Rule:
    - Applies ONLY to DC designation
    - Blocks Admin approval if DC has pending travel request for that date
    
    Returns:
        tuple: (can_approve: bool, error_message: str or None, remark: str or None)
    """
    
    # Rule applies ONLY to DC users
    if attendance.user.designation != 'DC':
        return (True, None, None)
    
    # Check if travel request exists for this date
    travel_request = TravelRequest.objects.filter(
        user=attendance.user,
        from_date__lte=attendance.date,
        to_date__gte=attendance.date
    ).first()
    
    # If no travel request exists, Admin approval allowed
    if not travel_request:
        return (True, None, None)
    
    # Check travel approval status
    if travel_request.status == 'pending':
        # Travel pending - Block Admin approval
        return (False, "Cannot approve DC attendance - Travel approval pending with Associate", "Travel Approval Pending")
    
    # Travel approved or rejected - Admin can approve
    return (True, None, None)


def log_blocked_dc_confirmation(dc_user, attendance, reason):
    """
    Logs blocked DC confirmation attempts for audit purposes.
    
    Args:
        dc_user: CustomUser who attempted confirmation
        attendance: Attendance record
        reason: Reason for blocking
    """
    from .models import SystemAuditLog
    
    SystemAuditLog.objects.create(
        actor=dc_user,
        action_type='BLOCKED_TRAVEL_PENDING',
        target_table='attendance',
        target_id=str(attendance.id),
        old_value={
            'user': attendance.user.employee_id,
            'date': str(attendance.date),
            'status': attendance.status,
            'is_confirmed_by_dc': attendance.is_confirmed_by_dc
        },
        new_value={
            'blocked_reason': reason,
            'timestamp': str(timezone.now())
        },
        ip_address='0.0.0.0',  # Will be updated by view
        device_info=f'DC Confirmation blocked for {attendance.user.employee_id}'
    )


def get_travel_status_for_attendance(attendance):
    """
    Gets travel request status for a given attendance record.
    
    Returns:
        dict: {
            'has_travel': bool,
            'status': str or None,
            'can_confirm': bool,
            'message': str or None
        }
    """
    
    # Check if travel request exists
    travel_request = TravelRequest.objects.filter(
        user=attendance.user,
        from_date__lte=attendance.date,
        to_date__gte=attendance.date
    ).first()
    
    if not travel_request:
        return {
            'has_travel': False,
            'status': None,
            'can_confirm': True,
            'message': None
        }
    
    can_confirm, error_message = validate_travel_approval_for_dc_confirmation(attendance)
    
    return {
        'has_travel': True,
        'status': travel_request.status,
        'can_confirm': can_confirm,
        'message': error_message
    }