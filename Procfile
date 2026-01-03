release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn Sat_Shine.wsgi --bind 0.0.0.0:$PORT --log-file -