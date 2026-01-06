web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn Sat_Shine.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate --noinput