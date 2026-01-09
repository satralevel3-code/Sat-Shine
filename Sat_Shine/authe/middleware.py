from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import JsonResponse
import logging
from pathlib import Path

User = get_user_model()
logger = logging.getLogger(__name__)

class DataPersistenceMiddleware(MiddlewareMixin):
    """Middleware to ensure data persistence and handle missing users"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_check = None
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check data integrity on admin requests"""
        try:
            # Only check on admin dashboard requests to avoid performance impact
            if request.path.startswith('/admin/') and request.user.is_authenticated:
                
                # Check if we have critical users
                admin_count = User.objects.filter(role='admin').count()
                field_count = User.objects.filter(role='field_officer').count()
                
                # If missing critical users, restore immediately
                if admin_count == 0 or field_count == 0:
                    logger.warning(f"Missing users detected: {admin_count} admins, {field_count} field officers")
                    
                    # Try to restore from backup
                    call_command('preserve_users', '--action=ensure', verbosity=0)
                    
                    # Recheck
                    admin_count = User.objects.filter(role='admin').count()
                    field_count = User.objects.filter(role='field_officer').count()
                    
                    logger.info(f"After restore: {admin_count} admins, {field_count} field officers")
        
        except Exception as e:
            logger.error(f"Data persistence check failed: {e}")
        
        return None
    
    def process_response(self, request, response):
        """Ensure backup exists after successful operations"""
        try:
            # Check if backup file exists
            backup_file = Path('persistent_data/users_persistent.json')
            
            # If no backup exists and we have users, create one
            if not backup_file.exists() and User.objects.exists():
                logger.info("No backup found, creating one...")
                call_command('preserve_users', '--action=backup', verbosity=0)
        
        except Exception as e:
            logger.error(f"Backup check failed: {e}")
        
        return response