@echo off
cd /d "C:\Users\admin\Git_demo\Sat_shine"
call env\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8000
pause