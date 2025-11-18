from ecommerce.wsgi import application
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

def handler(request, context):
    return application(request, context)