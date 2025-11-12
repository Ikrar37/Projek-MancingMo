from django.apps import AppConfig

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    verbose_name = 'Management Produk'  # Nama grup di admin
    
    def ready(self):
        # Import admin untuk mengubah label User model
        from django.contrib.auth.models import User
        
        # Ubah verbose_name untuk User model
        User._meta.verbose_name = 'Admin'
        User._meta.verbose_name_plural = 'Admin'