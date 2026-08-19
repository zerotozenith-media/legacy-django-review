#!/bin/sh

set -e

echo "Waiting for database to be ready..."
python manage.py wait_for_db

echo "Applying database migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input
