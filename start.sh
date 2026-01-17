#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# создаём суперюзера (если включено через Variables)
python manage.py ensure_superuser

exec gunicorn qazfinance_platform.wsgi:application --bind 0.0.0.0:${PORT}
