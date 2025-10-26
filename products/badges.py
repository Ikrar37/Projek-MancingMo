"""
Badges untuk menampilkan notifikasi di sidebar admin Unfold
✅ DIPERBAIKI: Gunakan nama model yang benar
"""

def order_badge(request):
    """
    Badge untuk menampilkan jumlah pesanan pending
    """
    from products.models import Order
    count = Order.objects.filter(status='pending').count()
    if count > 0:
        return f"{count} baru"
    return ""


def message_badge(request):
    """
    Badge untuk menampilkan jumlah pesan yang belum dibaca
    """
    from products.models import ContactMessage
    count = ContactMessage.objects.filter(is_read=False).count()
    if count > 0:
        return f"{count} baru"
    return ""