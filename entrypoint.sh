#!/bin/sh
set -e

# Production: run under config.settings.production (DEBUG=False) for both the
# management commands below and the gunicorn worker. Override via .env if needed.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

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

# --workers 6: report generation is the heavy, concurrent workload here and
# gunicorn sync workers handle one request each, so a single multi-second PDF
# used to block a third of the server. Six workers on 4 vCPU keeps page loads
# responsive while reports render; ~200 MB each, well inside the 6.7 GB free.
# --limit-request-line: report filters submit by GET and a hand-picked
# subset of the 348 MPs can run past gunicorn's 4094-byte default
# ("Request Line is too large"). 8190 is gunicorn's maximum; nginx is
# configured wider than that so it is never the narrower of the two.
echo "Starting gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-6}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --limit-request-line "${GUNICORN_LIMIT_REQUEST_LINE:-8190}" \
    --access-logfile - \
    --error-logfile -
