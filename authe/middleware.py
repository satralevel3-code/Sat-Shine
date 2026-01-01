from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import time

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Check if 30 minutes (1800 seconds) have passed
                if current_time - last_activity > 1800:
                    logout(request)
                    messages.warning(request, 'Your session has expired due to inactivity. Please log in again.')
                    return redirect(reverse('login'))
            
            # Update last activity time
            request.session['last_activity'] = current_time
        
        response = self.get_response(request)
        return response