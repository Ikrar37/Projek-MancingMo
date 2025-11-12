from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('verify-email/<str:username>/', views.verify_email, name='verify_email'),
    path('resend-verification/<str:username>/', views.resend_verification_code, name='resend_verification_code'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('midtrans-payment/<int:order_id>/', views.midtrans_payment, name='midtrans_payment'),
    path('midtrans-notification/', views.midtrans_notification, name='midtrans_notification'),
    path('continue-payment/<int:order_id>/', views.continue_payment, name='continue_payment'),
    path('retry-payment/<int:order_id>/', views.retry_payment, name='retry_payment'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),  # ✅ ROUTE BARU
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/orders/', views.order_history, name='order_history'),
    path('profile/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Cart
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/delete-selected/', views.delete_selected_items, name='delete_selected_items'),
    path('api/cart/count/', views.get_cart_count, name='get_cart_count'),
    
    path('cart/apply-voucher/', views.apply_voucher, name='apply_voucher'),
    path('cart/remove-voucher/', views.remove_voucher, name='remove_voucher'),

    # ✅ TAMBAHAN: Buy Now
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    
    # Reviews
    path('product/<int:product_id>/review/add/', views.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),

    path('admin/toggle-sidebar/', TemplateView.as_view(template_name='empty.html'), name='toggle_sidebar'),

    # Voucher AJAX routes
    path('checkout/apply-voucher/', views.apply_voucher_ajax, name='apply_voucher_ajax'),
    path('checkout/remove-voucher/', views.remove_voucher_ajax, name='remove_voucher_ajax'),
]