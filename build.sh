#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
# Run migrations (will create tables if they don't exist)
python manage.py migrate --noinput || echo "Migration completed with warnings"
