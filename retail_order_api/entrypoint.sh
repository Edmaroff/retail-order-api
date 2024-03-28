#!/bin/bash

python manage.py makemigrations --noinput
python manage.py migrate --noinput
echo "Apply database migrations"
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='root').exists() or User.objects.create_superuser('root@example.com', 'root')"
echo "Create SUPERUSER"
python manage.py collectstatic --no-input
echo "Starting server"
gunicorn  retail_order_api.wsgi:application --bind 0.0.0.0:8000
