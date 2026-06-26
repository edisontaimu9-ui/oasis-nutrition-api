#!/usr/bin/env bash
set -e

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Seeding sources..."
python manage.py seed_sources

echo "==> Starting gunicorn..."
exec gunicorn oasis_nutrition_api.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 1 \
  --timeout 120 \
  --log-level info
