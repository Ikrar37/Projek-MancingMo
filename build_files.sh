#!/bin/bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
# Hapus dulu staticfiles yang lama, lalu collect baru
rm -rf staticfiles
python manage.py collectstatic --noinput --clear

echo "Checking static files..."
find staticfiles -name "*.png" | head -10

echo "Build complete!"