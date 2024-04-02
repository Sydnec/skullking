#!/usr/bin/env bash

rm -rf */__pycache__
rm -rf */*/__pycache__
rm ./db.sqlite3
rm myapp/migrations/00*

python manage.py makemigrations myapp
python manage.py migrate
python manage.py loaddata users
python manage.py loaddata cards

./scripts/run.sh