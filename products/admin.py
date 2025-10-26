from django.contrib import admin
from .models import ProductReview
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, UserProfile, ShippingAddress,
    Cart, CartItem, Order, OrderItem, ContactMessage,
    AdminUser, CustomerUser  # Import proxy models
)

# ==================== UNREGISTER DEFAULT USER & GROUP ====================
# PENTING: Unregister User default agar tidak muncul menu "Users" yang gabungan
admin.site.unregister(User)
admin.site.unregister(Group)


# ==================== ADMIN USER ADMIN (HANYA ADMIN/STAFF) ====================

@admin.register(AdminUser)
class AdminUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'user_type', 'phone_display', 'city_display', 'date_joined']
    list_filter = ['is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone', 'profile__city']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informasi Login', {
            'fields': ('username', 'password')
        }),
        ('Informasi Personal', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Catatan: is_staff harus TRUE untuk Admin'
        }),
        ('Tanggal Penting', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Buat Admin Baru', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_superuser'),
            'description': 'is_staff akan otomatis di-set TRUE'
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    
    def get_queryset(self, request):
        """Override untuk hanya menampilkan admin/staff"""
        qs = super().get_queryset(request)
        return qs.filter(is_staff=True)
    
    def save_model(self, request, obj, form, change):
        """Override untuk memastikan is_staff=True saat membuat admin baru"""
        if not change:  # Jika membuat user baru
            obj.is_staff = True
        super().save_model(request, obj, form, change)
    
    def full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    full_name.short_description = 'Nama Lengkap'
    
    def user_type(self, obj):
        if obj.is_superuser:
            return format_html('<span style="background: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">SUPERUSER</span>')
        elif obj.is_staff:
            return format_html('<span style="background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">ADMIN</span>')
        return '-'
    user_type.short_description = 'Tipe User'
    
    def phone_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile.phone:
            return obj.profile.phone
        return '-'
    phone_display.short_description = 'Telepon'
    
    def city_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile.city:
            return obj.profile.city
        return '-'
    city_display.short_description = 'Kota'


# ==================== CUSTOMER USER ADMIN (HANYA CUSTOMER) ====================

@admin.register(CustomerUser)
class CustomerUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'phone_display', 'city_display', 'total_orders', 'date_joined']
    list_filter = ['is_active', 'date_joined', 'profile__gender', 'profile__city']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone', 'profile__whatsapp', 'profile__city']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informasi Login', {
            'fields': ('username', 'password')
        }),
        ('Informasi Personal', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Customer tidak memiliki akses admin'
        }),
        ('Tanggal Penting', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Buat Customer Baru', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
            'description': 'Customer tidak akan memiliki akses admin (is_staff=False)'
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    
    def get_queryset(self, request):
        """Override untuk hanya menampilkan customer (non-staff)"""
        qs = super().get_queryset(request)
        return qs.filter(is_staff=False)
    
    def save_model(self, request, obj, form, change):
        """Override untuk memastikan is_staff=False saat membuat customer baru"""
        if not change:  # Jika membuat user baru
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Customer dapat dihapus oleh admin"""
        return request.user.is_superuser
    
    def full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    full_name.short_description = 'Nama Lengkap'
    
    def phone_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile.phone:
            return obj.profile.phone
        return '-'
    phone_display.short_description = 'Telepon'
    
    def city_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile.city:
            return obj.profile.city
        return '-'
    city_display.short_description = 'Kota'
    
    def total_orders(self, obj):
        count = obj.orders.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} Pesanan</span>', count)
        return format_html('<span style="color: gray;">0 Pesanan</span>')
    total_orders.short_description = 'Total Pesanan'


# ==================== GROUP ADMIN ====================

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_users', 'permissions_count']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    
    def total_users(self, obj):
        count = obj.user_set.count()
        return f"{count} user(s)"
    total_users.short_description = 'Total Users'
    
    def permissions_count(self, obj):
        count = obj.permissions.count()
        return f"{count} permission(s)"
    permissions_count.short_description = 'Permissions'


# ==================== CATEGORY ADMIN ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'total_products', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Informasi Waktu', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def total_products(self, obj):
        count = obj.products.count()
        return f"{count} produk"
    total_products.short_description = 'Total Produk'


# ==================== PRODUCT ADMIN ====================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order']
    verbose_name = "Gambar Tambahan"
    verbose_name_plural = "Gambar Tambahan"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active', 'featured', 'created_at']
    list_filter = ['category', 'is_active', 'featured', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'featured', 'stock']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Harga & Stok', {
            'fields': ('price', 'stock')
        }),
        ('Gambar Utama', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active', 'featured')
        }),
        ('Informasi Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')


# ==================== USER PROFILE ADMIN ====================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'whatsapp', 'city', 'gender', 'created_at']
    list_filter = ['gender', 'city', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'whatsapp', 'city']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Informasi Kontak', {
            'fields': ('phone', 'whatsapp')
        }),
        ('Informasi Personal', {
            'fields': ('photo', 'birth_date', 'gender', 'bio')
        }),
        ('Alamat', {
            'fields': ('address', 'city', 'province', 'postal_code')
        }),
        ('Informasi Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


# ==================== SHIPPING ADDRESS ADMIN - DIHAPUS ====================
# ShippingAddress tidak perlu ditampilkan di admin karena data lengkap sudah ada di Order
# Jika suatu saat diperlukan lagi, uncomment kode di bawah ini:
#
# @admin.register(ShippingAddress)
# class ShippingAddressAdmin(admin.ModelAdmin):
#     list_display = ['user', 'full_name', 'phone', 'city', 'province', 'is_default', 'created_at']
#     list_filter = ['is_default', 'city', 'province', 'created_at']
#     search_fields = ['user__username', 'full_name', 'phone', 'city', 'address']
#     list_editable = ['is_default']
#     ordering = ['-created_at']
#     
#     fieldsets = (
#         ('User', {
#             'fields': ('user',)
#         }),
#         ('Informasi Penerima', {
#             'fields': ('full_name', 'phone')
#         }),
#         ('Alamat', {
#             'fields': ('address', 'city', 'province', 'postal_code')
#         }),
#         ('Status', {
#             'fields': ('is_default',)
#         }),
#         ('Informasi Waktu', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         }),
#     )
#     readonly_fields = ['created_at']
#     
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.select_related('user')


# ==================== CART ADMIN ====================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'quantity', 'subtotal_display']
    readonly_fields = ['subtotal_display']
    verbose_name = "Item di Keranjang"
    verbose_name_plural = "Item di Keranjang"
    
    def subtotal_display(self, obj):
        return f"Rp {obj.get_subtotal():,.0f}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items_display', 'total_price_display', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-updated_at']
    inlines = [CartItemInline]
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Informasi Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def total_items_display(self, obj):
        return f"{obj.total_items} item"
    total_items_display.short_description = 'Total Items'
    
    def total_price_display(self, obj):
        return f"Rp {obj.total_price:,.0f}"
    total_price_display.short_description = 'Total Price'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items')


# ==================== ORDER ADMIN ====================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'product_name', 'product_price', 'quantity', 'subtotal']
    readonly_fields = ['subtotal']
    verbose_name = "Item Pesanan"
    verbose_name_plural = "Item Pesanan"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'shipping_name', 'status', 'payment_method', 'total_display', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'updated_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_name', 'shipping_phone']
    list_editable = ['status']
    ordering = ['-created_at']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_province', 'shipping_postal_code')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_proof', 'paid_at')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    def total_display(self, obj):
        return f"Rp {obj.total:,.0f}"
    total_display.short_description = 'Total'
    total_display.admin_order_field = 'total'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items')
    
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='paid', paid_at=timezone.now())
        self.message_user(request, f'{updated} order(s) berhasil ditandai sebagai "Sudah Dibayar".')
    mark_as_paid.short_description = 'Tandai sebagai Sudah Dibayar'
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) berhasil ditandai sebagai "Sedang Diproses".')
    mark_as_processing.short_description = 'Tandai sebagai Sedang Diproses'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) berhasil ditandai sebagai "Dikirim".')
    mark_as_shipped.short_description = 'Tandai sebagai Dikirim'
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) berhasil ditandai sebagai "Terkirim".')
    mark_as_delivered.short_description = 'Tandai sebagai Terkirim'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} order(s) berhasil ditandai sebagai "Dibatalkan".')
    mark_as_cancelled.short_description = 'Tandai sebagai Dibatalkan'


# ==================== CONTACT MESSAGE ADMIN ====================

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject_display', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informasi Pengirim', {
            'fields': ('name', 'email', 'user')
        }),
        ('Pesan', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Informasi Waktu', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def subject_display(self, obj):
        return obj.subject if obj.subject else '(Tanpa Subjek)'
    subject_display.short_description = 'Subjek'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} pesan berhasil ditandai sebagai sudah dibaca.')
    mark_as_read.short_description = 'Tandai sebagai Sudah Dibaca'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} pesan berhasil ditandai sebagai belum dibaca.')
    mark_as_unread.short_description = 'Tandai sebagai Belum Dibaca'


# ==================== ADMIN SITE CUSTOMIZATION ====================

admin.site.site_header = 'MancingMo Admin'
admin.site.site_title = 'MancingMo Admin Portal'
admin.site.index_title = 'Selamat Datang di MancingMo Admin'

# ==================== PRODUCT REVIEW ADMIN ====================

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')
    readonly_fields = ('is_verified_purchase', 'created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('Informasi Review', {
            'fields': ('user', 'product', 'rating', 'comment')
        }),
        ('Status', {
            'fields': ('is_verified_purchase',)
        }),
        ('Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )