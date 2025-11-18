#!/bin/bash

echo "🔧 Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Buat migrations
python manage.py makemigrations

# Jalankan migrations  
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

echo "✅ Build completed successfully!"