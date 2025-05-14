#!/bin/sh

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Attempting to create superuser..."
python manage.py createsuperuser \
    --username "${DJANGO_SUPERUSER_USERNAME}" \
    --email "${DJANGO_SUPERUSER_EMAIL}" \
    --noinput || echo "Superuser creation attempt finished."

echo "Entrypoint finished after attempting superuser creation."
echo "IMPORTANT: Revert entrypoint.sh and redeploy to start the web server."
exit 0
