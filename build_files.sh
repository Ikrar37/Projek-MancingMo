#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Make migrations and migrate (optional - bisa di skip dulu)
# python manage.py makemigrations
# python manage.py migrate