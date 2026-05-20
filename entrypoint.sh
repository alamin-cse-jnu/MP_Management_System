#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME','mp_management'),
        user=os.environ.get('DB_USER','postgres'),
        password=os.environ.get('DB_PASSWORD','postgres'),
        host=os.environ.get('DB_HOST','db'),
        port=os.environ.get('DB_PORT','5432'),
    )
    print('  db ready')
except Exception as e:
    print(f'  not ready: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; do
  echo "  ...retrying in 2s"
  sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
