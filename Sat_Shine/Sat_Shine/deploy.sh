#!/bin/bash
# Production Deployment Script

echo "🚀 Starting SAT-SHINE Production Deployment..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser if needed (optional)
# python manage.py createsuperuser --noinput

echo "✅ Deployment complete!"
echo "🌐 Starting production server..."

# Start Gunicorn server
exec gunicorn Sat_Shine.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --log-level info