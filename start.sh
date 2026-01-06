#!/bin/bash
# Railway deployment script

echo "Starting SAT-SHINE deployment..."

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the server
echo "Starting server..."
gunicorn Sat_Shine.wsgi:application --bind 0.0.0.0:$PORT