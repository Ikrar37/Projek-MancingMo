#!/bin/bash

echo "=== Starting Build Process ==="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Making migrations..."
python manage.py makemigrations --noinput

echo "3. Running migrations..."
python manage.py migrate --noinput

echo "4. Collecting static files..."
rm -rf staticfiles
python manage.py collectstatic --noinput --clear

echo "5. Creating vercel output directory..."
mkdir -p /vercel/output/static

echo "6. Copying static files to Vercel output..."
cp -r staticfiles/* /vercel/output/static/ 2>/dev/null || echo "No static files to copy"

echo "7. Verifying files in output directory..."
find /vercel/output/static -type f -name "*.css" | head -10
find /vercel/output/static -type f -name "*.png" | head -10

echo "=== Build Complete ==="