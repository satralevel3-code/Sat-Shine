from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection

def home(request):
    return redirect('login')

def favicon(request):
    return HttpResponse(status=204)

def health_check(request):
    """Health check endpoint for Railway deployment monitoring"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'message': 'SAT-SHINE is running properly'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=500)
