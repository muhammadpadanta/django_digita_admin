#!/bin/sh

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn digita_admin.wsgi:application --bind 0.0.0.0:8000
