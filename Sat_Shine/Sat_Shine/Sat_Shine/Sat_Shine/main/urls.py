from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('favicon.ico', views.favicon, name='favicon'),
    path('health/', views.health_check, name='health_check'),
]