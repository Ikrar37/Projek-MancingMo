#!/bin/bash

echo "=== Starting Build Process ==="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Making migrations..."
python manage.py makemigrations --noinput

echo "3. Running migrations..."
python manage.py migrate --noinput

echo "4. Collecting static files..."
# Clear existing static files first
rm -rf staticfiles
python manage.py collectstatic --noinput --clear

echo "5. Verifying static files were collected..."
echo "=== Static files in staticfiles/ ==="
find staticfiles -type f -name "*.css" | head -10
find staticfiles -type f -name "*.js" | head -10
find staticfiles -type f -name "*.png" | head -10

echo "6. File structure:"
ls -la staticfiles/

echo "=== Build Complete ==="