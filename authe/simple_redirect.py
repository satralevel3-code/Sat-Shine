from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def employee_management_redirect(request):
    """Simple redirect that works"""
    try:
        return redirect('/auth/admin-dashboard/')
    except Exception as e:
        return HttpResponse(f'<h1>Employee Management</h1><p>Redirecting to dashboard...</p><script>window.location="/auth/admin-dashboard/";</script>')