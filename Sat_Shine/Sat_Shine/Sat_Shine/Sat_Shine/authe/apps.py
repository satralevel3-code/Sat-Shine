from django.apps import AppConfig


class AutheConfig(AppConfig):
    name = 'authe'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        import authe.signals