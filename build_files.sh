#!/bin/bash

echo "=== Starting Build Process ==="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Checking environment..."
echo "Python version: $(python --version)"
echo "Django version: $(python -c \"import django; print(django.get_version())\")"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "3. Making migrations..."
python manage.py makemigrations --noinput

echo "4. Running migrations..."
python manage.py migrate --noinput

echo "5. Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "6. Verifying static files..."
echo "=== Static files structure ==="
find staticfiles -type f | head -20
echo "=== CSS files ==="
find staticfiles -name "*.css" | head -10
echo "=== Image files ==="
find staticfiles -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" | head -10

echo "7. Checking if staticfiles directory exists..."
if [ -d "staticfiles" ]; then
    echo "✅ staticfiles directory exists"
    echo "Contents:"
    ls -la staticfiles/
else
    echo "❌ staticfiles directory does not exist"
fi

echo "=== Build Complete ==="