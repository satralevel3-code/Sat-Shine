# Enterprise DRF ViewSet with RBAC

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Attendance, CustomUser, AuditLog
from .attendance_rules import AttendanceRuleEngine
from .serializers import AttendanceSerializer

class RoleBasedPermission(permissions.BasePermission):
    """Enterprise role-based permission system"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Action-based permission mapping
        action_permissions = {
            'mark_attendance': ['field_officer', 'dc', 'mt', 'support', 'associate'],
            'confirm_dc': ['dc'],
            'approve_final': ['admin', 'hr', 'manager'],
            'override_attendance': ['super_admin'],
            'bulk_export': ['admin', 'hr', 'manager', 'super_admin']
        }
        
        required_roles = action_permissions.get(view.action, [])
        return request.user.role.name.lower() in required_roles
    
    def has_object_permission(self, request, view, obj):
        # Hierarchy enforcement
        if hasattr(obj, 'employee'):
            return self._can_access_employee_data(request.user, obj.employee)
        return True
    
    def _can_access_employee_data(self, user, target_employee):
        """Check if user can access target employee's data"""
        # Self access
        if user == target_employee:
            return True
            
        # Manager access to subordinates
        if target_employee.reporting_manager == user:
            return True
            
        # Admin/HR access to same DCCB
        if user.role.name in ['admin', 'hr'] and user.dccb == target_employee.dccb:
            return True
            
        # Super Admin access to all
        if user.role.name == 'super_admin':
            return True
            
        return False

class AttendanceViewSet(viewsets.ModelViewSet):
    """Enterprise attendance management API"""
    
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [RoleBasedPermission]
    
    @action(detail=False, methods=['post'])
    def mark_attendance(self, request):
        """Mark daily attendance with validation"""
        
        # Single attendance per day enforcement
        today = timezone.localdate()
        existing = Attendance.objects.filter(
            employee=request.user, 
            date=today
        ).first()
        
        if existing:
            return Response(
                {'error': 'Attendance already marked for today'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract request data
        attendance_status = request.data.get('status')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        workplace = request.data.get('workplace', 'office')
        travel_approved = request.data.get('travel_approved', False)
        
        # Business rule validation
        if attendance_status in ['present', 'half_day']:
            if not latitude or not longitude:
                return Response(
                    {'error': 'GPS location required for Present/Half Day'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate check-in rules
            is_valid, error_msg = AttendanceRuleEngine.validate_checkin_rules(
                employee_id=request.user.employee_id,
                travel_approved=travel_approved,
                workplace=workplace,
                latitude=float(latitude),
                longitude=float(longitude),
                dccb_lat=float(request.user.dccb.latitude),
                dccb_lng=float(request.user.dccb.longitude),
                geofence_radius=request.user.dccb.geofence_radius
            )
            
            if not is_valid:
                return Response(
                    {'error': error_msg}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create attendance record
        attendance = Attendance.objects.create(
            employee=request.user,
            date=today,
            status=attendance_status,
            check_in_time=timezone.localtime().time(),
            latitude=latitude,
            longitude=longitude,
            workplace=workplace,
            travel_approved=travel_approved
        )
        
        # Audit log
        AuditLog.objects.create(
            actor=request.user,
            action_type='ATTENDANCE_MARKED',
            target_table='attendance',
            target_id=str(attendance.id),
            new_value={
                'status': attendance_status,
                'time': attendance.check_in_time.isoformat(),
                'location': f"{latitude},{longitude}" if latitude else None
            },
            ip_address=self._get_client_ip(request)
        )
        
        return Response({
            'success': True,
            'attendance_id': attendance.id,
            'status': attendance_status,
            'check_in_time': attendance.check_in_time.strftime('%I:%M %p')
        })
    
    @action(detail=False, methods=['post'])
    def confirm_dc(self, request):
        """DC confirmation of team attendance"""
        
        if request.user.role.name != 'dc':
            return Response(
                {'error': 'DC role required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendance_ids = request.data.get('attendance_ids', [])
        confirmed_count = 0
        
        for att_id in attendance_ids:
            try:
                attendance = Attendance.objects.get(
                    id=att_id,
                    employee__reporting_manager=request.user,
                    dc_confirmed=False
                )
                attendance.dc_confirmed = True
                attendance.save()
                confirmed_count += 1
                
                # Audit log
                AuditLog.objects.create(
                    actor=request.user,
                    action_type='DC_CONFIRMED',
                    target_table='attendance',
                    target_id=str(attendance.id),
                    old_value={'dc_confirmed': False},
                    new_value={'dc_confirmed': True},
                    ip_address=self._get_client_ip(request)
                )
                
            except Attendance.DoesNotExist:
                continue
        
        return Response({
            'success': True,
            'confirmed_count': confirmed_count
        })
    
    def _get_client_ip(self, request):
        """Extract client IP for audit logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')