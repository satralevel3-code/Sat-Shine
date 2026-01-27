from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import CustomUser

@login_required
def test_employee_list(request):
    """Simple test view for employee list"""
    try:
        employees = CustomUser.objects.filter(role='field_officer')
        html = "<h1>Employee List Test</h1><ul>"
        for emp in employees:
            html += f"<li>{emp.employee_id} - {emp.first_name} {emp.last_name}</li>"
        html += "</ul>"
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")