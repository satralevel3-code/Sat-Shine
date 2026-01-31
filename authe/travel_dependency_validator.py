"""
Travel Dependency Validator - Enforces cross-module validation
CRITICAL: Prevents attendance approval when travel requests are pending/rejected
"""
from django.db import models
from .models import TravelRequest, Attendance

def validate_attendance_approval(attendance_record):
    """
    MANDATORY: Validate attendance approval against travel dependency
    Returns: (can_approve: bool, error_message: str, status_remark: str)
    """
    user = attendance_record.user
    date = attendance_record.date
    
    # Check for any travel requests covering this date
    conflicting_travel = TravelRequest.objects.filter(
        user=user,
        from_date__lte=date,
        to_date__gte=date,
        status__in=['pending', 'rejected']
    ).first()
    
    if conflicting_travel:
        if conflicting_travel.status == 'pending':
            return False, "Travel Approval Pending - Cannot approve attendance", "Travel Approval Pending"
        elif conflicting_travel.status == 'rejected':
            return False, "Travel Request Rejected - Cannot approve attendance", "Travel Not Approved"
    
    # Check if travel is approved
    approved_travel = TravelRequest.objects.filter(
        user=user,
        from_date__lte=date,
        to_date__gte=date,
        status='approved'
    ).exists()
    
    if approved_travel:
        return True, "", "Travel Approved"
    
    # No travel dependency
    return True, "", ""

def get_attendance_status_remark(attendance_record):
    """
    Get status remark for attendance record based on travel dependency
    """
    _, _, remark = validate_attendance_approval(attendance_record)
    return remark

def bulk_validate_attendance_approvals(attendance_queryset):
    """
    Validate multiple attendance records for bulk operations
    Returns: (approved_list, blocked_list)
    """
    approved = []
    blocked = []
    
    for attendance in attendance_queryset:
        can_approve, error_msg, _ = validate_attendance_approval(attendance)
        if can_approve:
            approved.append(attendance)
        else:
            blocked.append({
                'attendance': attendance,
                'error': error_msg
            })
    
    return approved, blocked