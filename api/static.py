import os
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def serve_static(request, path):
    """
    Serve static files manually for Vercel
    """
    # Security: prevent directory traversal
    if '..' in path or path.startswith('/'):
        return HttpResponseNotFound('File not found')
    
    # Build the full path to static file
    static_path = os.path.join(settings.BASE_DIR, 'staticfiles', path)
    
    # Check if file exists
    if os.path.exists(static_path) and os.path.isfile(static_path):
        # Determine content type
        content_type = 'application/octet-stream'
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif path.endswith('.svg'):
            content_type = 'image/svg+xml'
        
        response = FileResponse(open(static_path, 'rb'), content_type=content_type)
        return response
    
    return HttpResponseNotFound('File not found')