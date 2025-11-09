from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem, 
    ShippingAddress, ContactMessage, UserProfile, ProductReview, 
    EmailVerification, ShippingCost
)

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
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
            user=request.user if request.user.is_authenticated else None
        )
        
        messages.success(request, 'Pesan Anda berhasil dikirim! Kami akan segera menghubungi Anda.')
        return redirect('contact')
    
    return render(request, 'contact.html')


# ==================== AUTHENTICATION VIEWS ====================

# GANTI FUNGSI register() YANG ADA DI views.py DENGAN FUNGSI INI
# Letakkan di sekitar baris 248 (setelah fungsi contact)

def register(request):
    """View untuk registrasi user baru DENGAN EMAIL VERIFICATION"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validasi input
        if not all([first_name, last_name, username, email, password1, password2]):
            messages.error(request, 'Semua field wajib diisi!')
            return render(request, 'registration/register.html')
        
        if password1 != password2:
            messages.error(request, 'Password tidak cocok!')
            return render(request, 'registration/register.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password harus minimal 8 karakter!')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email sudah terdaftar!')
            return render(request, 'registration/register.html')
        
        try:
            # Buat user baru (is_active=False sampai email diverifikasi)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # User tidak aktif sampai verifikasi email
            )
            
            # Buat email verification record
            email_verification = EmailVerification.objects.create(user=user)
            verification_code = email_verification.generate_code()
            
            # Kirim email verifikasi
            try:
                send_mail(
                    subject='Verifikasi Email - MancingMo',
                    message=f'''
Halo {first_name},

Terima kasih telah mendaftar di MancingMo!

Kode verifikasi Anda adalah: {verification_code}

Kode ini akan expired dalam 24 jam.

Silakan masukkan kode ini di halaman verifikasi untuk mengaktifkan akun Anda.

Salam,
Tim MancingMo
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                messages.success(request, f'Registrasi berhasil! Kode verifikasi telah dikirim ke {email}. Silakan cek email Anda.')
                return redirect('verify_email', username=username)
                
            except Exception as e:
                # Jika gagal kirim email, hapus user dan tampilkan error
                user.delete()
                messages.error(request, f'Gagal mengirim email verifikasi. Silakan coba lagi. Error: {str(e)}')
                return render(request, 'registration/register.html')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            return render(request, 'registration/register.html')
    
    return render(request, 'registration/register.html')  # ← KEMBALIKAN KE TEMPLATE ASLI


def verify_email(request, username):
    """View untuk halaman verifikasi email"""
    user = get_object_or_404(User, username=username)
    
    # Jika user sudah verified, redirect ke login
    if user.is_active:
        messages.info(request, 'Email Anda sudah diverifikasi. Silakan login.')
        return redirect('login')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, 'Kode verifikasi wajib diisi!')
            return render(request, 'registration/verify_email.html', {'username': username, 'user': user})
        
        try:
            email_verification = user.email_verification
            success, message = email_verification.verify(code)
            
            if success:
                messages.success(request, message)
                return redirect('login')
            else:
                messages.error(request, message)
        except EmailVerification.DoesNotExist:
            messages.error(request, 'Data verifikasi tidak ditemukan!')
    
    return render(request, 'registration/verify_email.html', {'username': username, 'user': user})


def resend_verification_code(request, username):
    """View untuk kirim ulang kode verifikasi"""
    user = get_object_or_404(User, username=username)
    
    if user.is_active:
        messages.info(request, 'Email Anda sudah diverifikasi.')
        return redirect('login')
    
    try:
        email_verification = user.email_verification
        verification_code = email_verification.generate_code()
        
        # Kirim ulang email
        send_mail(
            subject='Kode Verifikasi Baru - MancingMo',
            message=f'''
Halo {user.first_name},

Kode verifikasi baru Anda adalah: {verification_code}

Kode ini akan expired dalam 24 jam.

Salam,
Tim MancingMo
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        messages.success(request, f'Kode verifikasi baru telah dikirim ke {user.email}')
    except Exception as e:
        messages.error(request, f'Gagal mengirim email. Error: {str(e)}')
    
    return redirect('verify_email', username=username)


def login_view(request):
    """View untuk halaman login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Akun Anda belum diverifikasi. Silakan verifikasi email Anda terlebih dahulu.')
                return redirect('verify_email', username=username)
            
            login(request, user)
            next_url = request.GET.get('next', 'home')
            messages.success(request, f'Selamat datang kembali, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Username atau password salah!')
    
    return render(request, 'registration/login.html')


def logout_view(request):
    """View untuk logout"""
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('home')


@login_required
def profile(request):
    """View untuk halaman profile user dengan statistik lengkap"""
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Calculate statistics
    total_orders = Order.objects.filter(user=request.user).count()
    
    # Get cart items count
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items_count = cart.items.count()
    except Cart.DoesNotExist:
        cart_items_count = 0
    
    # Calculate total spending (dari order yang sudah selesai/delivered)
    total_spending = Order.objects.filter(
        user=request.user,
        status__in=['paid', 'processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'profile': user_profile,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'cart_items_count': cart_items_count,
        'total_spending': total_spending,
    }
    
    return render(request, 'registration/profile.html', context)


@login_required
def edit_profile(request):
    """View untuk edit profile - DENGAN DROPDOWN ALAMAT"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user data
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update profile data
        user_profile.phone = request.POST.get('phone', '')
        user_profile.address = request.POST.get('address', '')
        user_profile.province = request.POST.get('province', '')
        user_profile.city = request.POST.get('city', '')
        user_profile.district = request.POST.get('district', '')
        user_profile.postal_code = request.POST.get('postal_code', '')
        user_profile.bio = request.POST.get('bio', '')
        
        # Handle birth_date
        birth_date = request.POST.get('birth_date', '')
        if birth_date:
            user_profile.birth_date = birth_date
        else:
            user_profile.birth_date = None
        
        # Handle gender
        gender = request.POST.get('gender', '')
        if gender:
            user_profile.gender = gender
        else:
            user_profile.gender = ''
        
        # Handle photo upload
        if 'photo' in request.FILES:
            user_profile.photo = request.FILES['photo']
        
        user_profile.save()
        
        messages.success(request, 'Profile berhasil diperbarui!')
        return redirect('profile')
    
    context = {
        'profile': user_profile,
    }
    
    return render(request, 'registration/edit_profile.html', context)

@login_required
def change_password(request):
    """View untuk halaman change password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password Anda berhasil diubah!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/change_password.html', {'form': form})


@login_required
def order_history(request):
    """View untuk halaman riwayat pesanan dengan pengecekan status Midtrans real-time"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # ✅ CEK STATUS MIDTRANS UNTUK SEMUA ORDER PENDING
    from .midtrans_utils import MidtransPayment
    midtrans = MidtransPayment()
    
    for order in orders:
        if order.status == 'pending' and order.payment_method == 'midtrans' and order.midtrans_order_id:
            try:
                status_result = midtrans.check_transaction_status(order.midtrans_order_id)
                
                if status_result['success']:
                    transaction_status = status_result['data'].get('transaction_status')
                    fraud_status = status_result['data'].get('fraud_status')
                    
                    if transaction_status == 'capture':
                        if fraud_status == 'accept':
                            order.status = 'paid'
                            order.paid_at = timezone.now()
                    elif transaction_status == 'settlement':
                        order.status = 'paid'
                        order.paid_at = timezone.now()
                    elif transaction_status in ['deny', 'expire', 'cancel']:
                        order.midtrans_transaction_status = transaction_status
                    
                    order.save()
                    
            except Exception as e:
                print(f"Error checking Midtrans status for order {order.id}: {str(e)}")
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
    }
    
    return render(request, 'registration/order_history.html', context)


@login_required
def order_detail(request, order_id):
    """View untuk detail pesanan dengan pengecekan status Midtrans real-time"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # ✅ CEK STATUS TRANSAKSI MIDTRANS JIKA ORDER MASIH PENDING
    if order.status == 'pending' and order.payment_method == 'midtrans' and order.midtrans_order_id:
        from .midtrans_utils import MidtransPayment
        
        try:
            midtrans = MidtransPayment()
            status_result = midtrans.check_transaction_status(order.midtrans_order_id)
            
            if status_result['success']:
                transaction_status = status_result['data'].get('transaction_status')
                fraud_status = status_result['data'].get('fraud_status')
                
                # Update status order berdasarkan response Midtrans
                if transaction_status == 'capture':
                    if fraud_status == 'accept':
                        order.status = 'paid'
                        order.paid_at = timezone.now()
                elif transaction_status == 'settlement':
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                elif transaction_status in ['deny', 'expire', 'cancel']:
                    # Update status transaksi ke expired/cancelled
                    order.midtrans_transaction_status = transaction_status
                
                # Simpan perubahan
                order.save()
                
        except Exception as e:
            # Jika gagal cek status, lanjutkan saja tanpa error
            print(f"Error checking Midtrans status: {str(e)}")
    
    context = {
        'order': order,
    }
    
    return render(request, 'registration/order_detail.html', context)


# ==================== CART VIEWS ====================

@login_required
def cart(request):
    """View untuk halaman cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    
    return render(request, 'cart.html', context)


@login_required
@require_POST
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

# Tambahkan fungsi ini di views.py setelah fungsi remove_from_cart()
# Letakkan di sekitar baris 689 (setelah fungsi remove_from_cart)

@login_required
@require_POST
def delete_selected_items(request):
    """View untuk menghapus multiple items dari keranjang (AJAX)"""
    import json
    
    try:
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        
        if not item_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'Tidak ada produk yang dipilih!'
            })
        
        # Hapus items yang dipilih
        deleted_count = CartItem.objects.filter(
            id__in=item_ids,
            cart__user=request.user
        ).delete()[0]
        
        if deleted_count > 0:
            return JsonResponse({
                'status': 'success',
                'message': f'{deleted_count} produk berhasil dihapus dari keranjang!',
                'deleted_count': deleted_count
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Produk tidak ditemukan atau sudah terhapus!'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Format data tidak valid!'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        })


# ✅ FUNGSI BARU: BUY NOW
@login_required
@require_POST
def buy_now(request, product_id):
    """View untuk beli sekarang - langsung ke checkout tanpa masuk keranjang"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
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
    
    # Simpan data produk dan quantity ke session untuk checkout
    request.session['buy_now_data'] = {
        'product_id': product.id,
        'quantity': quantity
    }
    
    # Response untuk AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'redirect_url': '/checkout/'
        })
    
    # Redirect langsung ke checkout
    return redirect('checkout')


# ==================== CHECKOUT VIEWS ====================

@login_required
def checkout(request):
    """View untuk halaman checkout - SUPPORT BUY NOW & CART ITEMS DENGAN ONGKIR PER KECAMATAN"""
    
    # ✅ CEK APAKAH INI DARI BUY NOW
    buy_now_data = request.session.get('buy_now_data')
    is_buy_now = buy_now_data is not None
    
    if is_buy_now:
        # Mode: Beli Sekarang (langsung dari product detail)
        product = get_object_or_404(Product, id=buy_now_data['product_id'], is_active=True)
        quantity = buy_now_data['quantity']
        
        # Validasi stock
        if quantity > product.stock:
            messages.error(request, f'Stock {product.name} tidak mencukupi!')
            del request.session['buy_now_data']
            return redirect('product_detail', slug=product.slug)
        
        # Buat structure yang mirip dengan cart items untuk konsistensi
        class BuyNowItem:
            def __init__(self, product, quantity):
                self.id = f"buynow_{product.id}"
                self.product = product
                self.quantity = quantity
            
            def get_subtotal(self):
                return self.product.price * self.quantity
        
        cart_items = [BuyNowItem(product, quantity)]
        cart_total = product.price * quantity
        
    else:
        # Mode: Checkout dari keranjang
        cart = get_object_or_404(Cart, user=request.user)
        
        # Validasi cart tidak kosong
        if not cart.items.exists():
            messages.error(request, 'Keranjang Anda kosong!')
            return redirect('cart')
        
        # Ambil selected items dari POST atau session
        selected_item_ids = request.POST.getlist('selected_items') or request.session.get('selected_items', [])
        
        if not selected_item_ids:
            messages.error(request, 'Pilih minimal 1 produk untuk checkout!')
            return redirect('cart')
        
        # Filter cart items berdasarkan selected items
        cart_items = cart.items.filter(id__in=selected_item_ids)
        
        if not cart_items.exists():
            messages.error(request, 'Produk yang dipilih tidak valid!')
            return redirect('cart')
        
        cart_total = sum(item.get_subtotal() for item in cart_items)
    
    # Ambil profile user untuk auto-fill
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Ambil alamat default dari ShippingAddress (jika ada)
    default_address = ShippingAddress.objects.filter(user=request.user, is_default=True).first()
    
    # Ambil daftar kecamatan untuk dropdown
    kecamatan_list = ShippingCost.objects.filter(is_active=True).order_by('kecamatan')
    
    # Hitung shipping cost default (rata-rata)
    from django.db.models import Avg
    default_shipping_cost = ShippingCost.objects.filter(is_active=True).aggregate(
        avg_harga=Avg('harga')
    )['avg_harga'] or Decimal('10000')
    
    shipping_cost = default_shipping_cost
    
    if request.method == 'POST':
        # Ambil data dari form
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        province = request.POST.get('province', '').strip()
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        payment_method = 'midtrans'  # ✅ HARDCODED ke midtrans
        save_address = request.POST.get('save_address')
        
        # Validasi data wajib
        if not all([full_name, phone, address, city, district]):
            messages.error(request, 'Mohon lengkapi semua data wajib termasuk kecamatan!')
            if not is_buy_now:
                request.session['selected_items'] = selected_item_ids
            return redirect('checkout')
        
        # Hitung shipping cost berdasarkan kecamatan yang dipilih
        try:
            shipping_cost_obj = ShippingCost.objects.get(kecamatan=district, is_active=True)
            shipping_cost = shipping_cost_obj.harga
        except ShippingCost.DoesNotExist:
            # Jika kecamatan tidak ditemukan, gunakan default
            shipping_cost = default_shipping_cost
            messages.warning(request, f'Ongkir untuk kecamatan {district} tidak ditemukan, menggunakan tarif default.')
        
        # Validasi stock sebelum membuat order
        for item in cart_items:
            if item.quantity > item.product.stock:
                messages.error(request, f'Stock {item.product.name} tidak mencukupi! Tersisa {item.product.stock} item.')
                if not is_buy_now:
                    request.session['selected_items'] = selected_item_ids
                return redirect('checkout')
        
        # Hitung total
        subtotal = cart_total
        total = subtotal + shipping_cost
        
        try:
            # Buat order
            order = Order.objects.create(
                user=request.user,
                shipping_name=full_name,
                shipping_phone=phone,
                shipping_address=address,
                shipping_province=province,
                shipping_city=city,
                shipping_district=district,
                shipping_postal_code=postal_code,
                payment_method=payment_method,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total=total,
                status='pending'
            )
            
            # Buat order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_price=item.product.price,
                    quantity=item.quantity,
                    subtotal=item.get_subtotal()
                )
                
                # Kurangi stock produk
                item.product.stock -= item.quantity
                item.product.save()
            
            # Simpan alamat jika diminta
            if save_address:
                ShippingAddress.objects.filter(user=request.user).update(is_default=False)
                ShippingAddress.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone,
                    address=address,
                    province=province,
                    city=city,
                    district=district,
                    postal_code=postal_code,
                    is_default=True
                )
            
            # ✅ INTEGRASI MIDTRANS - Langsung create transaction
            from .midtrans_utils import MidtransPayment
            
            midtrans = MidtransPayment()
            result = midtrans.create_transaction(order)
            
            if result['success']:
                # Simpan snap token ke order
                order.midtrans_snap_token = result['snap_token']
                order.midtrans_order_id = order.order_number
                order.save()
                
                # ✅ CLEANUP berdasarkan mode
                if is_buy_now:
                    # Hapus buy_now_data dari session
                    del request.session['buy_now_data']
                else:
                    # Hapus selected cart items
                    CartItem.objects.filter(id__in=selected_item_ids).delete()
                    # Clear session
                    if 'selected_items' in request.session:
                        del request.session['selected_items']
                
                # Redirect ke payment page dengan snap token
                return redirect('midtrans_payment', order_id=order.id)
            else:
                # Jika gagal membuat transaksi Midtrans, kembalikan stock
                for item in order.items.all():
                    item.product.stock += item.quantity
                    item.product.save()
                
                order.delete()
                messages.error(request, f'Gagal membuat transaksi: {result["error"]}')
                if not is_buy_now:
                    request.session['selected_items'] = selected_item_ids
                return redirect('checkout')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan saat membuat pesanan: {str(e)}')
            if not is_buy_now:
                request.session['selected_items'] = selected_item_ids
            return redirect('checkout')
    
    # GET request - tampilkan halaman checkout
    if not is_buy_now and 'selected_items' in request.session and request.method == 'GET':
        del request.session['selected_items']
    
    context = {
        'cart_items': cart_items,
        'user_profile': user_profile,
        'default_address': default_address,
        'kecamatan_list': kecamatan_list,
        'shipping_cost': shipping_cost,
        'subtotal': cart_total,
        'total': cart_total + shipping_cost,
        'is_buy_now': is_buy_now,
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

@login_required
def midtrans_payment(request, order_id):
    """View untuk halaman pembayaran Midtrans"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Pastikan order menggunakan Midtrans dan punya snap token
    if order.payment_method != 'midtrans' or not order.midtrans_snap_token:
        messages.error(request, 'Order ini tidak menggunakan pembayaran Midtrans!')
        return redirect('order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'snap_token': order.midtrans_snap_token,
        'client_key': settings.MIDTRANS_CLIENT_KEY,
        'is_production': settings.MIDTRANS_IS_PRODUCTION,
    }
    
    return render(request, 'midtrans_payment.html', context)

@login_required
def continue_payment(request, order_id):
    """View untuk melanjutkan pembayaran order yang masih pending"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Validasi: hanya order dengan status pending yang bisa lanjut bayar
    if order.status != 'pending':
        messages.error(request, 'Order ini tidak dapat dilanjutkan pembayarannya!')
        return redirect('order_detail', order_id=order.id)
    
    # Validasi: harus menggunakan metode pembayaran midtrans
    if order.payment_method != 'midtrans':
        messages.error(request, 'Order ini tidak menggunakan pembayaran Midtrans!')
        return redirect('order_detail', order_id=order.id)
    
    # Jika sudah punya snap token, langsung redirect ke halaman payment
    if order.midtrans_snap_token:
        return redirect('midtrans_payment', order_id=order.id)
    
    # Jika belum punya snap token, buat baru
    from .midtrans_utils import MidtransPayment
    
    try:
        midtrans = MidtransPayment()
        result = midtrans.create_transaction(order)
        
        if result['success']:
            # Simpan snap token ke order
            order.midtrans_snap_token = result['snap_token']
            order.midtrans_order_id = order.order_number
            order.save()
            
            # Redirect ke payment page
            return redirect('midtrans_payment', order_id=order.id)
        else:
            messages.error(request, f'Gagal membuat transaksi: {result["error"]}')
            return redirect('order_detail', order_id=order.id)
            
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('order_detail', order_id=order.id)

@login_required
def retry_payment(request, order_id):
    """View untuk membuat transaksi pembayaran baru jika yang lama expired"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Validasi: hanya order dengan status pending yang bisa retry
    if order.status != 'pending':
        messages.error(request, 'Order ini tidak dapat diproses ulang!')
        return redirect('order_detail', order_id=order.id)
    
    # Validasi: harus menggunakan metode pembayaran midtrans
    if order.payment_method != 'midtrans':
        messages.error(request, 'Order ini tidak menggunakan pembayaran Midtrans!')
        return redirect('order_detail', order_id=order.id)
    
    # Buat transaksi Midtrans baru (akan generate snap token baru)
    from .midtrans_utils import MidtransPayment
    
    try:
        midtrans = MidtransPayment()
        result = midtrans.create_transaction(order)
        
        if result['success']:
            # Update order dengan snap token baru
            order.midtrans_snap_token = result['snap_token']
            order.midtrans_order_id = order.order_number
            order.midtrans_transaction_status = 'pending'  # Reset status ke pending
            order.save()
            
            messages.success(request, 'Transaksi pembayaran baru berhasil dibuat!')
            # Redirect ke payment page
            return redirect('midtrans_payment', order_id=order.id)
        else:
            messages.error(request, f'Gagal membuat transaksi baru: {result["error"]}')
            return redirect('order_detail', order_id=order.id)
            
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('order_detail', order_id=order.id)


@login_required
@require_POST
def cancel_order(request, order_id):
    """View untuk membatalkan pesanan"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Validasi: hanya order dengan status pending yang bisa dibatalkan
    if order.status != 'pending':
        messages.error(request, 'Hanya pesanan dengan status menunggu pembayaran yang dapat dibatalkan!')
        return redirect('order_detail', order_id=order.id)
    
    try:
        # Kembalikan stock produk
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
        
        # Update status order menjadi cancelled
        order.status = 'cancelled'
        order.save()
        
        messages.success(request, 'Pesanan berhasil dibatalkan. Stock produk telah dikembalikan.')
        return redirect('order_detail', order_id=order.id)
        
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan saat membatalkan pesanan: {str(e)}')
        return redirect('order_detail', order_id=order.id)


@require_POST
def midtrans_notification(request):
    """
    Webhook handler untuk notifikasi dari Midtrans
    Midtrans akan mengirim POST request ke endpoint ini setiap ada perubahan status transaksi
    """
    import json
    from django.views.decorators.csrf import csrf_exempt
    from django.utils import timezone
    
    try:
        # Parse notification data
        notification = json.loads(request.body.decode('utf-8'))
        
        order_id = notification.get('order_id')
        transaction_status = notification.get('transaction_status')
        fraud_status = notification.get('fraud_status')
        transaction_id = notification.get('transaction_id')
        payment_type = notification.get('payment_type')
        
        # Cari order berdasarkan order_id
        try:
            order = Order.objects.get(order_number=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
        
        # Update order dengan data dari Midtrans
        order.midtrans_transaction_id = transaction_id
        order.midtrans_transaction_status = transaction_status
        order.midtrans_payment_type = payment_type
        
        # Handle transaction status
        if transaction_status == 'capture':
            if fraud_status == 'accept':
                order.status = 'paid'
                order.paid_at = timezone.now()
        elif transaction_status == 'settlement':
            order.status = 'paid'
            order.paid_at = timezone.now()
        elif transaction_status == 'pending':
            order.status = 'pending'
        elif transaction_status in ['deny', 'expire', 'cancel']:
            order.status = 'cancelled'
            # Kembalikan stock jika dibatalkan
            for item in order.items.all():
                item.product.stock += item.quantity
                item.product.save()
        
        order.save()
        
        return JsonResponse({'status': 'success'}, status=200)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ==================== AJAX HELPER ====================

@login_required
def get_cart_count(request):
    """API endpoint untuk mendapatkan jumlah item di cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        count = cart.get_unique_items_count()
    except Cart.DoesNotExist:
        count = 0
    
    return JsonResponse({'count': count})