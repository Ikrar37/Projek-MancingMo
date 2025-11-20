#!/bin/bash

echo "=== Starting Build Process ==="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Making migrations..."
python manage.py makemigrations --noinput

echo "3. Running migrations..."
python manage.py migrate --noinput

echo "4. Checking static files structure..."
echo "=== Static files in static/ ==="
find static -type f | head -20

echo "5. Collecting static files..."
rm -rf staticfiles
python manage.py collectstatic --noinput --clear

echo "6. Verifying collected static files..."
echo "=== Files in staticfiles/ ==="
ls -la staticfiles/
echo "=== CSS files ==="
find staticfiles -name "*.css" | head -10
echo "=== Image files ==="
find staticfiles -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" | head -10

echo "=== Build Complete ==="