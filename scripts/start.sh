#!/bin/sh
# Container entrypoint: apply migrations (optional) and start Gunicorn.
#
# Environment:
#   PORT                    Port to bind (Railway sets this; default 8000)
#   DJANGO_MIGRATE_ON_START Set to 0 to skip `migrate`, e.g. when migrations
#                           run as a separate release/pre-deploy step or when
#                           several replicas start at once.
#   WEB_CONCURRENCY         Number of Gunicorn workers (read by Gunicorn itself)
set -eu

if [ "${DJANGO_MIGRATE_ON_START:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

# exec so Gunicorn becomes PID 1 and receives SIGTERM directly.
exec gunicorn core.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --access-logfile - \
    --error-logfile -
