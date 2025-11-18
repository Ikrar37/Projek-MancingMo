#!/bin/bash

echo "🔧 Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Buat dan jalankan migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

echo "✅ Build completed successfully!"