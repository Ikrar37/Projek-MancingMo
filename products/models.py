from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.validators import MinValueValidator

# ==================== CATEGORY MODEL ====================

class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nama Kategori")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    
    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ['name']
        app_label = 'products'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


# ==================== PRODUCT MODEL ====================

class Product(models.Model):
    name = models.CharField(max_length=300, verbose_name="Nama Produk")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Deskripsi")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Harga")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Kategori")
    stock = models.IntegerField(default=0, verbose_name="Stok")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Gambar")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    featured = models.BooleanField(default=False, verbose_name="Unggulan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")
    
    class Meta:
        verbose_name = "Produk"
        verbose_name_plural = "Produk"
        ordering = ['-created_at']
        app_label = 'products'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    def get_main_image(self):
        first_image = self.images.first()
        if first_image:
            return first_image.image.url
        if self.image:
            return self.image.url
        return None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Produk")
    image = models.ImageField(upload_to='products/', verbose_name="Gambar")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Teks Alternatif")
    order = models.IntegerField(default=0, verbose_name="Urutan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    
    class Meta:
        verbose_name = "Gambar Produk"
        verbose_name_plural = "Gambar Produk"
        ordering = ['order', 'created_at']
        app_label = 'products'
    
    def __str__(self):
        return f"{self.product.name} - Gambar {self.order}"
    

    # ==================== EMAIL VERIFICATION MODEL (BARU) ====================

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification', verbose_name="Pengguna")
    verification_code = models.CharField(max_length=6, verbose_name="Kode Verifikasi")
    is_verified = models.BooleanField(default=False, verbose_name="Sudah Diverifikasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Diverifikasi Pada")
    
    class Meta:
        verbose_name = "Verifikasi Email"
        verbose_name_plural = "Verifikasi Email"
        app_label = 'products'
    
    def __str__(self):
        return f"{self.user.username} - {'Verified' if self.is_verified else 'Pending'}"
    
    def generate_code(self):
        """Generate kode verifikasi 6 digit"""
        self.verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.save()
        return self.verification_code
    
    def is_expired(self):
        """Cek apakah kode sudah expired (24 jam)"""
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiry_time
    
    def verify(self, code):
        """Verifikasi kode"""
        if self.is_expired():
            return False, "Kode verifikasi sudah kadaluarsa. Silakan minta kode baru."
        
        if self.verification_code == code:
            self.is_verified = True
            self.verified_at = timezone.now()
            self.user.is_active = True
            self.user.save()
            self.save()
            return True, "Email berhasil diverifikasi!"
        
        return False, "Kode verifikasi salah!"


# ==================== USER PROFILE MODEL ====================

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Pengguna")
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name="Foto Profile")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Nomor Telepon")
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name="Nomor WhatsApp")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Tanggal Lahir")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Jenis Kelamin")
    address = models.TextField(blank=True, verbose_name="Alamat Lengkap")
    province = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    city = models.CharField(max_length=100, blank=True, verbose_name="Kota/Kabupaten")
    district = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos")
    bio = models.TextField(blank=True, verbose_name="Bio/Deskripsi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")
    
    class Meta:
        verbose_name = "Profile Pengguna"
        verbose_name_plural = "Profile Pengguna"
        app_label = 'products'
    
    def __str__(self):
        return f"Profile - {self.user.username}"
    
    def get_full_address(self):
        parts = []
        if self.address:
            parts.append(self.address)
        if self.district:
            parts.append(self.district)
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts) if parts else "Alamat belum diisi"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ==================== SHIPPING ADDRESS MODEL ====================

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses', verbose_name="Pengguna")
    full_name = models.CharField(max_length=200, verbose_name="Nama Lengkap")
    phone = models.CharField(max_length=20, verbose_name="Nomor Telepon")
    address = models.TextField(verbose_name="Alamat")
    province = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    city = models.CharField(max_length=100, verbose_name="Kota/Kabupaten")
    district = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos")
    is_default = models.BooleanField(default=False, verbose_name="Alamat Utama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    
    class Meta:
        verbose_name = "Alamat Pengiriman"
        verbose_name_plural = "Alamat Pengiriman"
        app_label = 'products'
    
    def __str__(self):
        return f"{self.full_name} - {self.city}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


# ==================== CART MODEL ====================

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Pengguna")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")
    
    class Meta:
        verbose_name = "Keranjang"
        verbose_name_plural = "Keranjang"
        app_label = 'products'
    
    def __str__(self):
        return f"Keranjang - {self.user.username}"
    
    @property
    def total_items(self):
        """Menghitung total kuantitas semua item (jumlah barang)"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """Alias untuk get_total()"""
        return self.get_total()
    
    @property
    def unique_items_count(self):
        """Menghitung jumlah produk unik di cart"""
        return self.items.count()
    
    def get_total(self):
        """Menghitung total harga semua item"""
        return sum(item.get_subtotal() for item in self.items.all())
    
    def get_item_count(self):
        """Method ini menghitung kuantitas total"""
        return self.total_items
    
    def get_unique_items_count(self):
        """Method untuk menghitung jumlah produk unik"""
        return self.unique_items_count


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Keranjang")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produk")
    quantity = models.IntegerField(default=1, verbose_name="Jumlah")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Ditambahkan Pada")
    
    class Meta:
        verbose_name = "Item Keranjang"
        verbose_name_plural = "Item Keranjang"
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    @property
    def subtotal(self):
        return self.product.price * self.quantity
    
    def get_subtotal(self):
        return self.subtotal


# ==================== ORDER MODEL ====================

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('paid', 'Sudah Dibayar'),
        ('processing', 'Sedang Diproses'),
        ('shipped', 'Dikirim'),
        ('delivered', 'Terkirim'),
        ('cancelled', 'Dibatalkan'),
        ('ready_for_pickup', 'Siap Diambil'),
    ]
    
    PAYMENT_CHOICES = [
        ('midtrans', 'Midtrans Payment Gateway'),
        ('bank_transfer', 'Transfer Bank'),
        ('qris', 'QRIS'),
        ('cod', 'Cash on Delivery'),
    ]

    SHIPPING_METHODS = [
        ('delivery', 'Delivery (Dikirim)'),
        ('pickup', 'Pick Up (Ambil Sendiri)'),
    ]

    SHIPPING_TYPES = [
        ('reguler', 'Reguler'),
        ('express', 'Express'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Pengguna")
    order_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Pesanan")
    midtrans_order_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Midtrans Order ID")
    midtrans_transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Midtrans Transaction ID")
    midtrans_transaction_status = models.CharField(max_length=50, blank=True, null=True, verbose_name="Status Transaksi Midtrans")
    midtrans_payment_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipe Pembayaran Midtrans")
    midtrans_snap_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Snap Token")
    
    shipping_method = models.CharField(
        max_length=20, 
        choices=SHIPPING_METHODS, 
        default='delivery',
        verbose_name="Metode Pengiriman"
    )
    
    shipping_name = models.CharField(max_length=200, verbose_name="Nama Penerima")
    shipping_phone = models.CharField(max_length=20, verbose_name="Telepon Penerima")
    shipping_address = models.TextField(verbose_name="Alamat Pengiriman")
    shipping_province = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    shipping_city = models.CharField(max_length=100, verbose_name="Kota/Kabupaten")
    shipping_district = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan")
    shipping_postal_code = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos")
    shipping_type = models.CharField(max_length=20, choices=SHIPPING_TYPES, default='reguler')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name="Metode Pembayaran")
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True, verbose_name="Bukti Pembayaran")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Subtotal")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Ongkos Kirim")
    voucher = models.ForeignKey('Voucher', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Voucher")
    voucher_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Kode Voucher")
    voucher_discount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Diskon Voucher")
    total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Total")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Dibayar Pada")
    
    class Meta:
        verbose_name = "Pesanan"
        verbose_name_plural = "Pesanan"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pesanan {self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import datetime
            date_str = datetime.datetime.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(order_number__startswith=f'ORD-{date_str}').order_by('-order_number').first()
            if last_order:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.order_number = f'ORD-{date_str}-{new_number:05d}'
        
        if self.shipping_method == 'pickup' and self.status == 'paid':
            self.status = 'ready_for_pickup'
            
        super().save(*args, **kwargs)
    
    @property
    def is_pickup(self):
        return self.shipping_method == 'pickup'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Pesanan")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Produk")
    product_name = models.CharField(max_length=300, verbose_name="Nama Produk")
    product_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Harga Produk")
    quantity = models.IntegerField(default=1, verbose_name="Jumlah")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Subtotal")
    
    class Meta:
        verbose_name = "Item Pesanan"
        verbose_name_plural = "Item Pesanan"
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.product_price * self.quantity
        super().save(*args, **kwargs)


# ==================== CONTACT MESSAGE MODEL ====================

class ContactMessage(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nama")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=300, blank=True, verbose_name="Subjek")
    message = models.TextField(verbose_name="Pesan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Dikirim")
    is_read = models.BooleanField(default=False, verbose_name="Sudah Dibaca")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pengguna")
    
    class Meta:
        verbose_name = "Pesan Kontak"
        verbose_name_plural = "Pesan Kontak"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject if self.subject else 'Tanpa Subjek'}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

# ==================== SHIPPING COST MODEL ====================

class ShippingCost(models.Model):
    kecamatan = models.CharField(max_length=100, unique=True, verbose_name="Kecamatan")
    harga = models.DecimalField(max_digits=10, decimal_places=0, default=10000, verbose_name="Harga Ongkir")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")
    
    class Meta:
        verbose_name = "Biaya Pengiriman"
        verbose_name_plural = "Biaya Pengiriman"
        ordering = ['kecamatan']
        app_label = 'products'
    
    def __str__(self):
        return f"{self.kecamatan} - Rp {self.harga}"
    
# ==================== VOUCHER MODEL ====================

class Voucher(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=20, unique=True, verbose_name="Kode Voucher")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage', verbose_name="Tipe Diskon")
    discount_value = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="Nilai Diskon")
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, validators=[MinValueValidator(0)], verbose_name="Minimum Belanja")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Maksimal Diskon")
    valid_from = models.DateTimeField(verbose_name="Berlaku Dari")
    valid_to = models.DateTimeField(verbose_name="Berlaku Sampai")
    usage_limit = models.PositiveIntegerField(default=1, verbose_name="Batas Penggunaan")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Jumlah Digunakan")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    
    class Meta:
        verbose_name = "Voucher"
        verbose_name_plural = "Voucher"
        ordering = ['-created_at']
        app_label = 'products'
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ''}"
    
    def is_valid(self, cart_total=0):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            self.used_count < self.usage_limit and
            cart_total >= self.min_purchase_amount
        )
    
    def calculate_discount(self, cart_total):
        if not self.is_valid(cart_total):
            return 0
        
        if self.discount_type == 'percentage':
            discount = (self.discount_value / 100) * cart_total
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        else:
            discount = min(self.discount_value, cart_total)
        
        return discount
    
    def use_voucher(self):
        if self.used_count < self.usage_limit:
            self.used_count += 1
            self.save()
            return True
        return False
    
# ==================== PRODUCT REVIEW MODEL ====================

class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 - Sangat Buruk'),
        (2, '2 - Buruk'),
        (3, '3 - Cukup'),
        (4, '4 - Bagus'),
        (5, '5 - Sangat Bagus'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Produk")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Pengguna")
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="Rating")
    comment = models.TextField(verbose_name="Komentar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")
    is_verified_purchase = models.BooleanField(default=False, verbose_name="Pembelian Terverifikasi")
    
    class Meta:
        verbose_name = "Review Produk"
        verbose_name_plural = "Review Produk"
        ordering = ['-created_at']
        unique_together = ('product', 'user')
        app_label = 'products'
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}⭐)"
    
    def save(self, *args, **kwargs):
        has_purchased = OrderItem.objects.filter(
            order__user=self.user,
            product=self.product,
            order__status__in=['paid', 'processing', 'shipped', 'delivered']
        ).exists()
        
        self.is_verified_purchase = has_purchased
        super().save(*args, **kwargs)


# ==================== PROXY MODELS FOR ADMIN SEPARATION ====================

class AdminUser(User):
    class Meta:
        proxy = True
        verbose_name = "Admin"
        verbose_name_plural = "Admin"
        app_label = 'auth'


class CustomerUser(User):
    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "User"
        app_label = 'auth'