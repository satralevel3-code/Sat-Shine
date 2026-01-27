from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.management import call_command
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def backup_on_user_save(sender, instance, created, **kwargs):
    """Automatically backup users when any user is created or updated"""
    try:
        if created:
            logger.info(f"New user created: {instance.employee_id}, triggering backup")
        else:
            logger.info(f"User updated: {instance.employee_id}, triggering backup")
        
        # Run backup in background
        call_command('preserve_users', '--action=backup', verbosity=0)
        
    except Exception as e:
        logger.error(f"Auto-backup failed: {e}")

@receiver(post_delete, sender=User)
def backup_on_user_delete(sender, instance, **kwargs):
    """Automatically backup users when any user is deleted"""
    try:
        logger.info(f"User deleted: {instance.employee_id}, triggering backup")
        call_command('preserve_users', '--action=backup', verbosity=0)
        
    except Exception as e:
        logger.error(f"Auto-backup on delete failed: {e}")