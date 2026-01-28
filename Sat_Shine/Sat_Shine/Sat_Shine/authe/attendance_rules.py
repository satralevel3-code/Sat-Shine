# Attendance Rule Engine - Core Business Logic

from datetime import time, datetime, timedelta
from typing import Tuple, Optional

class AttendanceRuleEngine:
    """Enterprise attendance rule processing"""
    
    # Time windows
    ON_TIME_CUTOFF = time(10, 0)      # 10:00 AM
    LATE_CUTOFF = time(14, 30)        # 2:30 PM  
    CHECKOUT_START = time(18, 0)      # 6:00 PM
    CHECKOUT_END = time(23, 0)        # 11:00 PM
    
    @classmethod
    def calculate_attendance_status(
        cls, 
        checkin_time: Optional[time],
        checkout_time: Optional[time],
        travel_approved: bool = False,
        leave_approved: bool = False,
        dc_confirmed: bool = False
    ) -> Tuple[str, str]:
        """
        Calculate final attendance status and timing
        Returns: (status, timing_status)
        """
        
        # Leave approved = Absent
        if leave_approved:
            return 'absent', 'leave_approved'
            
        # No check-in = Absent (unless DC confirms)
        if not checkin_time:
            if dc_confirmed:
                return 'present', 'dc_confirmed'
            return 'absent', 'not_marked'
            
        # Check-in timing rules
        if checkin_time <= cls.ON_TIME_CUTOFF:
            timing_status = 'on_time'
        elif checkin_time <= cls.LATE_CUTOFF:
            timing_status = 'late'
        else:
            # After 2:30 PM = Half Day
            return 'half_day', 'late_checkin'
            
        # Checkout validation
        if not checkout_time:
            # Missed checkout = Half Day
            return 'half_day', 'missed_checkout'
            
        # Valid checkout window check
        if not (cls.CHECKOUT_START <= checkout_time <= cls.CHECKOUT_END):
            return 'half_day', 'invalid_checkout'
            
        # Full day present
        return 'present', timing_status
    
    @classmethod
    def validate_checkin_rules(
        cls,
        employee_id: str,
        travel_approved: bool,
        workplace: str,
        latitude: float,
        longitude: float,
        dccb_lat: float,
        dccb_lng: float,
        geofence_radius: int = 200
    ) -> Tuple[bool, str]:
        """
        Validate check-in business rules
        Returns: (is_valid, error_message)
        """
        
        # Travel validation
        if not travel_approved and workplace != 'office':
            return False, "Travel approval required for non-office locations"
            
        # Geo-fencing (advisory for now)
        distance = cls._calculate_distance(latitude, longitude, dccb_lat, dccb_lng)
        if distance > geofence_radius and not travel_approved:
            return False, f"Location {distance}m from office. Travel approval required."
            
        return True, ""
    
    @classmethod
    def _calculate_distance(cls, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Haversine distance calculation in meters"""
        import math
        
        R = 6371000  # Earth radius in meters
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

# Example usage:
# status, timing = AttendanceRuleEngine.calculate_attendance_status(
#     checkin_time=time(9, 30),
#     checkout_time=time(18, 30),
#     travel_approved=True
# )
# Result: ('present', 'on_time')