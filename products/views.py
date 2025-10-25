# products/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from .models import Product, Category, Cart, CartItem, Order, OrderItem, ShippingAddress, ContactMessage, UserProfile, ProductReview
from django.db.models import Avg
from decimal import Decimal
from django.contrib.auth.forms import PasswordChangeForm

# ==================== PUBLIC VIEWS ====================

def home(request):
    """View untuk halaman home - Menampilkan 8 produk terbaru"""
    products = Product.objects.filter(is_active=True)[:8]
    
    context = {
        'products': products,
    }
    
    return render(request, 'home.html', context)


def shop(request):
    """View untuk halaman shop (daftar semua produk)"""
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    categories = Category.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Filter berdasarkan kategori jika ada
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        products = products.filter(category__slug=category_slug)
        selected_category = category_slug
    
    # Pagination - 16 products per page
    paginator = Paginator(products, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
    }
    
    return render(request, 'shop.html', context)


def product_detail(request, slug):
    """View untuk halaman detail produk dengan review"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Ambil semua reviews untuk produk ini
    reviews = product.reviews.select_related('user', 'user__profile').all()
    
    # Hitung rating rata-rata dan jumlah review
    rating_stats = product.reviews.aggregate(
        average=Avg('rating'),
        total=Count('id')
    )
    
    # Cek apakah user sudah pernah review
    user_review = None
    can_review = False
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()
        
        # User bisa review jika sudah pernah beli dan belum pernah review
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status__in=['paid', 'processing', 'shipped', 'delivered']
        ).exists()
        
        can_review = has_purchased and not user_review
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'rating_stats': rating_stats,
        'user_review': user_review,
        'can_review': can_review,
    }
    
    return render(request, 'product_detail.html', context)


# TAMBAHKAN fungsi-fungsi baru untuk review:

@login_required
@require_POST
def add_review(request, product_id):
    """View untuk menambahkan review produk"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Cek apakah user sudah pernah review
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.error(request, 'Anda sudah memberikan review untuk produk ini!')
        return redirect('product_detail', slug=product.slug)
    
    # Cek apakah user pernah membeli produk ini
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__status__in=['paid', 'processing', 'shipped', 'delivered']
    ).exists()
    
    if not has_purchased:
        messages.error(request, 'Anda harus membeli produk ini terlebih dahulu untuk memberikan review!')
        return redirect('product_detail', slug=product.slug)
    
    # Ambil data dari form
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    
    # Validasi
    if not rating or not comment:
        messages.error(request, 'Rating dan komentar wajib diisi!')
        return redirect('product_detail', slug=product.slug)
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, 'Rating tidak valid!')
        return redirect('product_detail', slug=product.slug)
    
    # Buat review
    ProductReview.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        comment=comment
    )
    
    messages.success(request, 'Review berhasil ditambahkan! Terima kasih atas feedback Anda.')
    return redirect('product_detail', slug=product.slug)


@login_required
@require_POST
def edit_review(request, review_id):
    """View untuk mengedit review"""
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    
    # Validasi
    if not rating or not comment:
        messages.error(request, 'Rating dan komentar wajib diisi!')
        return redirect('product_detail', slug=review.product.slug)
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, 'Rating tidak valid!')
        return redirect('product_detail', slug=review.product.slug)
    
    # Update review
    review.rating = rating
    review.comment = comment
    review.save()
    
    messages.success(request, 'Review berhasil diperbarui!')
    return redirect('product_detail', slug=review.product.slug)


@login_required
@require_POST
def delete_review(request, review_id):
    """View untuk menghapus review"""
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product_slug = review.product.slug
    review.delete()
    
    messages.success(request, 'Review berhasil dihapus!')
    return redirect('product_detail', slug=product_slug)


def about(request):
    """View untuk halaman about"""
    return render(request, 'about.html')


def contact(request):
    """View untuk halaman contact dengan form handling"""
    
    if request.method == 'POST':
        # Ambil data dari form
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validasi data
        if not name or not email or not message:
            messages.error(request, 'Mohon lengkapi semua field yang wajib diisi!')
            context = {
                'form_data': {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message,
                }
            }
            return render(request, 'contact.html', context)
        
        # Validasi email format (basic)
        if '@' not in email or '.' not in email:
            messages.error(request, 'Format email tidak valid!')
            context = {
                'form_data': {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message,
                }
            }
            return render(request, 'contact.html', context)
        
        # Simpan pesan ke database
        try:
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
                user=request.user if request.user.is_authenticated else None
            )
            
            messages.success(request, f'Terima kasih {name}! Pesan Anda telah berhasil dikirim. Tim kami akan segera menghubungi Anda.')
            return redirect('contact')
            
        except Exception as e:
            messages.error(request, 'Terjadi kesalahan saat mengirim pesan. Silakan coba lagi.')
            context = {
                'form_data': {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message,
                }
            }
            return render(request, 'contact.html', context)
    
    return render(request, 'contact.html')


# ==================== AUTH VIEWS ====================

def user_login(request):
    """View untuk login user"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Username atau password salah!')
    
    return render(request, 'registration/login.html')


def user_register(request):
    """View untuk register user baru"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validasi password
        if password1 != password2:
            messages.error(request, 'Password tidak cocok!')
            return render(request, 'registration/register.html')
        
        # Validasi username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return render(request, 'registration/register.html')
        
        # Validasi email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email sudah terdaftar!')
            return render(request, 'registration/register.html')
        
        # Buat user baru
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        
        messages.success(request, 'Akun berhasil dibuat! Silakan login.')
        return redirect('login')
    
    return render(request, 'registration/register.html')


def user_logout(request):
    """View untuk logout user"""
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('home')


# ==================== PROFILE VIEWS (NEW) ====================

@login_required
def profile(request):
    """View untuk halaman profile user - Dashboard Overview"""
    user = request.user
    
    # Pastikan user memiliki profile (auto-create jika belum ada)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Hitung statistik user
    cart_items = 0
    if hasattr(user, 'cart'):
        cart_items = user.cart.items.count()
    
    # Data statistik dari Order model
    total_orders = Order.objects.filter(user=user).count()
    
    # Total spent (hanya order yang sudah dibayar/delivered)
    orders = Order.objects.filter(user=user, status__in=['paid', 'processing', 'shipped', 'delivered'])
    total_spent = sum(order.total for order in orders)
    
    context = {
        'profile': profile,
        'total_orders': total_orders,
        'cart_items': cart_items,
        'total_spent': total_spent,
    }
    
    return render(request, 'registration/profile.html', context)


@login_required
def edit_profile(request):
    """View untuk edit profile user"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update User model fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update UserProfile fields
        profile.phone = request.POST.get('phone', '')
        profile.whatsapp = request.POST.get('whatsapp', '')
        
        # Handle birth_date
        birth_date = request.POST.get('birth_date', '')
        if birth_date:
            profile.birth_date = birth_date
        else:
            profile.birth_date = None
            
        profile.gender = request.POST.get('gender', '')
        profile.address = request.POST.get('address', '')
        profile.city = request.POST.get('city', '')
        profile.province = request.POST.get('province', '')
        profile.postal_code = request.POST.get('postal_code', '')
        profile.bio = request.POST.get('bio', '')
        
        # Handle photo upload
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        
        profile.save()
        
        messages.success(request, 'Profile berhasil diperbarui!')
        return redirect('profile')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'registration/edit_profile.html', context)


@login_required
def change_password(request):
    """View untuk ubah password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            messages.success(request, 'Password berhasil diubah!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/change_password.html', {'form': form})


@login_required
def order_history(request):
    """View untuk melihat riwayat pesanan"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination - 10 orders per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
    }
    
    return render(request, 'registration/order_history.html', context)


@login_required
def order_detail(request, order_number):
    """View untuk detail pesanan"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'registration/order_detail.html', context)


@login_required
@require_POST
def cancel_order(request, order_number):
    """View untuk membatalkan pesanan"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        
        # Kembalikan stock produk
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
        
        messages.success(request, f'Pesanan #{order_number} berhasil dibatalkan.')
    else:
        messages.error(request, 'Pesanan tidak dapat dibatalkan.')
    
    return redirect('order_history')


# ==================== CART VIEWS ====================

@login_required
def cart(request):
    """View untuk halaman keranjang"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    
    return render(request, 'cart.html', context)


@login_required
def add_to_cart(request, product_id):
    """View untuk menambah produk ke keranjang - SUPPORT AJAX"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Validasi stock
    if quantity > product.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Stock {product.name} tidak mencukupi!'
            })
        messages.error(request, f'Stock {product.name} tidak mencukupi!')
        return redirect('product_detail', slug=product.slug)
    
    # Cek apakah produk sudah ada di cart
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not item_created:
        # Jika sudah ada, tambahkan quantity
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Stock {product.name} tidak mencukupi!'
                })
            messages.error(request, f'Stock {product.name} tidak mencukupi!')
            return redirect('product_detail', slug=product.slug)
        cart_item.quantity = new_quantity
        cart_item.save()
    
    # ✅ DIPERBAIKI: Response untuk AJAX - Menghitung produk unik bukan total kuantitas
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} berhasil ditambahkan ke keranjang!',
            'cart_count': cart.get_unique_items_count(),
            'cart_total': float(cart.get_total())
        })
    
    messages.success(request, f'{product.name} berhasil ditambahkan ke keranjang!')
    return redirect('cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    """View untuk mengupdate quantity item di keranjang (AJAX)"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
            status = 'success'
            message = 'Quantity berhasil ditambah'
        else:
            status = 'error'
            message = 'Stock tidak mencukupi'
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            status = 'success'
            message = 'Quantity berhasil dikurangi'
        else:
            status = 'error'
            message = 'Quantity minimal 1'
    else:
        status = 'error'
        message = 'Invalid action'
    
    return JsonResponse({
        'status': status,
        'message': message,
        'quantity': cart_item.quantity,
        'subtotal': float(cart_item.get_subtotal()),
        'cart_total': float(cart_item.cart.get_total()),
    })


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """View untuk menghapus item dari keranjang"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'{product_name} berhasil dihapus dari keranjang!')
    return redirect('cart')


# ==================== CHECKOUT VIEWS ====================

# GANTI fungsi checkout yang lama dengan ini:

@login_required
def checkout(request):
    """View untuk halaman checkout - Terintegrasi dengan UserProfile"""
    cart = get_object_or_404(Cart, user=request.user)
    
    # Validasi cart tidak kosong
    if not cart.items.exists():
        messages.error(request, 'Keranjang Anda kosong!')
        return redirect('cart')
    
    # Ambil profile user untuk auto-fill
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Ambil alamat default dari ShippingAddress (jika ada)
    default_address = ShippingAddress.objects.filter(user=request.user, is_default=True).first()
    
    # Hitung estimasi pengiriman (contoh: 10.000 flat rate)
    shipping_cost = Decimal('10000')
    
    if request.method == 'POST':
        # Ambil data dari form
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        province = request.POST.get('province', '')  # ✅ TAMBAHAN BARU
        postal_code = request.POST.get('postal_code', '')
        payment_method = request.POST.get('payment_method')
        save_address = request.POST.get('save_address')
        
        # Validasi data (province opsional tapi direkomendasikan)
        if not all([full_name, phone, address, city, payment_method]):
            messages.error(request, 'Mohon lengkapi semua data wajib!')
            return redirect('checkout')
        
        # Hitung total
        subtotal = cart.get_total()
        total = subtotal + shipping_cost
        
        # Buat order
        order = Order.objects.create(
            user=request.user,
            shipping_name=full_name,
            shipping_phone=phone,
            shipping_address=address,
            shipping_city=city,
            shipping_province=province,  # ✅ TAMBAHAN BARU
            shipping_postal_code=postal_code,
            payment_method=payment_method,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            status='pending'
        )
        
        # Buat order items dari cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity,
                subtotal=cart_item.get_subtotal()
            )
            
            # Kurangi stock produk
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()
        
        # Simpan alamat jika diminta
        if save_address:
            ShippingAddress.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city,
                province=province,  # ✅ TAMBAHAN BARU
                postal_code=postal_code,
                is_default=True
            )
        
        # Hapus cart items
        cart.items.all().delete()
        
        # Redirect ke halaman order success
        messages.success(request, f'Pesanan berhasil dibuat! Nomor Order: {order.order_number}')
        return redirect('order_success', order_id=order.id)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'user_profile': user_profile,  # ✅ TAMBAHAN BARU
        'default_address': default_address,
        'shipping_cost': shipping_cost,
        'total': cart.get_total() + shipping_cost,
    }
    
    return render(request, 'checkout.html', context)


@login_required
def order_success(request, order_id):
    """View untuk halaman order berhasil"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'order_success.html', context)


# ==================== AJAX HELPER ====================

@login_required
def get_cart_count(request):
    """API endpoint untuk mendapatkan jumlah item di cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        # ✅ DIPERBAIKI: Menghitung produk unik bukan total kuantitas
        count = cart.get_unique_items_count()
    except Cart.DoesNotExist:
        count = 0
    
    return JsonResponse({'count': count})