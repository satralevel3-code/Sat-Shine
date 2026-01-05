@echo off
REM Windows development server for SAT-SHINE

echo Starting SAT-SHINE Development Server...
cd Sat_shine
set DJANGO_SETTINGS_MODULE=Sat_Shine.settings.development
env\Scripts\python.exe manage.py runserver 127.0.0.1:8000