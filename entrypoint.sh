#!/bin/sh

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn home_fixer.wsgi:application --bind 0.0.0.0:$PORT