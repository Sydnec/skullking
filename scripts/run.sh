#!/usr/bin/env bash

PORT=8000

# python manage.py makemigrations myapp
# # Run migrations
python manage.py migrate

python manage.py runserver ${PORT}
