"""
Django settings for ecommerce project.
Optimized for Vercel deployment.
"""

from pathlib import Path
import os
import ssl
import certifi
import dj_database_url
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== ENVIRONMENT CONFIGURATION ====================
# Deteksi apakah running di Vercel
IS_VERCEL = os.environ.get('VERCEL_ENV') is not None

# Security settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)

# Allowed hosts
if IS_VERCEL:
    ALLOWED_HOSTS = ['.vercel.app', '.now.sh']
    # Tambahkan domain custom Anda di sini jika ada
    custom_domain = config('CUSTOM_DOMAIN', default='')
    if custom_domain:
        ALLOWED_HOSTS.append(custom_domain)
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# ==================== APPLICATION DEFINITION ====================
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party apps
    'cloudinary_storage',
    'cloudinary',
    
    # Local apps
    'products',
]

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # COMMENT DULU
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

# ==================== TEMPLATES CONFIGURATION ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.csrf',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# ==================== DATABASE CONFIGURATION ====================
if IS_VERCEL:
    # Database untuk production (PostgreSQL)
    database_url = config('DATABASE_URL')
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Database untuk development (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==================== PASSWORD VALIDATION ====================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Makassar'
USE_I18N = True
USE_TZ = True

USE_L10N = False
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
NUMBER_GROUPING = 3

# ==================== STATIC FILES CONFIGURATION ====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Pastikan ini di settings.py
DEBUG = False  # Atau dari environment variable

# ==================== SECURITY SETTINGS ====================
if IS_VERCEL:
    # Security settings untuk production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    CSRF_TRUSTED_ORIGINS = [
        'https://*.vercel.app',
        'https://*.now.sh',
    ]
    
    # Tambahkan custom domain jika ada
    custom_domain = config('CUSTOM_DOMAIN', default='')
    if custom_domain:
        CSRF_TRUSTED_ORIGINS.append(f'https://{custom_domain}')
else:
    # Development settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# ==================== AUTHENTICATION ====================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'profile'
LOGOUT_REDIRECT_URL = 'home'

# ==================== EMAIL CONFIGURATION ====================
# Fix SSL untuk Python
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

_ssl_context = ssl.create_default_context(cafile=certifi.where())
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=f'MancingMo <{config("EMAIL_HOST_USER", default="")}>')
EMAIL_TIMEOUT = 30

# Monkey patch untuk email SSL
import django.core.mail.backends.smtp
import smtplib

original_starttls = django.core.mail.backends.smtp.EmailBackend.open

def patched_open(self):
    """Patched open method dengan custom SSL context"""
    try:
        if self.connection:
            return False
        connection_params = {'host': self.host, 'port': self.port}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params['context'] = _ssl_context
        try:
            self.connection = self.connection_class(**connection_params)
            if not self.use_ssl and self.use_tls:
                self.connection.starttls(context=_ssl_context)
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except (OSError, smtplib.SMTPException):
            if not self.fail_silently:
                raise
            return False
    except Exception:
        return original_starttls(self)

django.core.mail.backends.smtp.EmailBackend.open = patched_open

# ==================== MIDTRANS CONFIGURATION ====================
MIDTRANS_SERVER_KEY = config('MIDTRANS_SERVER_KEY', default='')
MIDTRANS_CLIENT_KEY = config('MIDTRANS_CLIENT_KEY', default='')
MIDTRANS_IS_PRODUCTION = config('MIDTRANS_IS_PRODUCTION', default=False, cast=bool)
MIDTRANS_IS_SANITIZED = True
MIDTRANS_IS_3DS = True

# ==================== DJANGO UNFOLD CONFIGURATION ====================
def environment_callback(request):
    """Callback untuk environment badge di admin"""
    if DEBUG:
        return ["Development", "danger"]
    return ["Production", "success"]

def dashboard_callback(request, context):
    """Callback untuk custom dashboard stats"""
    try:
        from products.models import Order, Product
        from django.db.models import Sum
        
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(
            status='delivered'
        ).aggregate(total=Sum('total'))['total'] or 0
        total_products = Product.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        context.update({
            "custom_stats": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_products": total_products,
                "pending_orders": pending_orders,
            }
        })
    except Exception as e:
        # Jika terjadi error, skip saja (misalnya saat first deploy)
        pass
    
    return context

UNFOLD = {
    "SITE_TITLE": "MancingMo Admin",
    "SITE_HEADER": "MancingMo Dashboard",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: "/static/image/logo mancingmo.png",
        "dark": lambda request: "/static/image/logo mancingmo.png",
    },
    "SITE_LOGO": {
        "light": lambda request: "/static/image/logo mancingmo.png",
        "dark": lambda request: "/static/image/logo mancingmo.png",
    },
    "SITE_SYMBOL": "shopping_cart",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "ecommerce.settings.environment_callback",
    "DASHBOARD_CALLBACK": "ecommerce.settings.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": lambda request: "/admin/",
                    },
                ],
            },
            {
                "title": "Manajemen Produk",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Kategori",
                        "icon": "category",
                        "link": lambda request: "/admin/products/category/",
                    },
                    {
                        "title": "Produk",
                        "icon": "inventory_2",
                        "link": lambda request: "/admin/products/product/",
                    },
                    {
                        "title": "Gambar Produk",
                        "icon": "image",
                        "link": lambda request: "/admin/products/productimage/",
                    },
                    {
                        "title": "Voucher",
                        "icon": "local_offer",
                        "link": lambda request: "/admin/products/voucher/",
                    },
                    {
                        "title": "Biaya Pengiriman",
                        "icon": "local_shipping",
                        "link": lambda request: "/admin/products/shippingcost/",
                    },
                ],
            },
            {
                "title": "Transaksi",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Pesanan",
                        "icon": "shopping_bag",
                        "link": lambda request: "/admin/products/order/",
                    },
                    {
                        "title": "Keranjang",
                        "icon": "shopping_cart",
                        "link": lambda request: "/admin/products/cart/",
                    },
                ],
            },
            {
                "title": "Pelanggan",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Admin",
                        "icon": "admin_panel_settings",
                        "link": lambda request: "/admin/auth/adminuser/",
                    },
                    {
                        "title": "Customer",
                        "icon": "people",
                        "link": lambda request: "/admin/auth/customeruser/",
                    },
                    {
                        "title": "Profile Pengguna",
                        "icon": "person",
                        "link": lambda request: "/admin/products/userprofile/",
                    },
                    {
                        "title": "Alamat Pengiriman",
                        "icon": "location_on",
                        "link": lambda request: "/admin/products/shippingaddress/",
                    },
                    {
                        "title": "Review Produk",
                        "icon": "star",
                        "link": lambda request: "/admin/products/productreview/",
                    },
                    {
                        "title": "Verifikasi Email",
                        "icon": "mark_email_read",
                        "link": lambda request: "/admin/products/emailverification/",
                    },
                ],
            },
            {
                "title": "Komunikasi",
                "separator": True,
                "items": [
                    {
                        "title": "Pesan Kontak",
                        "icon": "email",
                        "link": lambda request: "/admin/products/contactmessage/",
                    },
                ],
            },
        ],
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== LOGGING (OPTIONAL - Untuk debugging di Vercel) ====================
if IS_VERCEL:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }