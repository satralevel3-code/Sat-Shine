#!/bin/bash
set -e

echo "Starting SAT-SHINE deployment..."

# Run migrations first
echo "Running database migrations..."
python manage.py migrate --noinput

# Ensure users exist (backup + restore + create defaults)
echo "Ensuring user data persistence..."
python manage.py preserve_users --action=ensure

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn Sat_Shine.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -