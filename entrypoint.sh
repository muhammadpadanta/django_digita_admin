#!/bin/sh

# Script ini memastikan database siap dan menjalankan migrasi
# sebelum memulai server Django.

# Cek apakah variabel environment DB_HOST ada
if [ -z "$DB_HOST" ]; then
    echo "Error: DB_HOST environment variable is not set."
    exit 1
fi
if [ -z "$DB_PORT" ]; then
    echo "Error: DB_PORT environment variable is not set."
    exit 1
fi

echo "Waiting for postgres..."

sleep 5

echo "PostgreSQL started"

# migrasi database
echo "Running database migrations..."
python manage.py migrate --noinput

exec "$@"
