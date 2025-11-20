#!/bin/bash

echo "=== Starting Build Process ==="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Making migrations..."
python manage.py makemigrations --noinput

echo "3. Running migrations..."
python manage.py migrate --noinput

echo "4. Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "5. Listing static files..."
find staticfiles -name "*.css" | head -10

echo "=== Build Complete ==="