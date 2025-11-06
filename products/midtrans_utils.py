# products/midtrans_utils.py
# FILE BARU - Buat file ini di folder products/

import midtransclient
from django.conf import settings
from decimal import Decimal


class MidtransPayment:
    """
    Utility class untuk integrasi Midtrans Snap Payment
    """
    
    def __init__(self):
        # Inisialisasi Snap API
        self.snap = midtransclient.Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY,
            client_key=settings.MIDTRANS_CLIENT_KEY
        )
    
    def create_transaction(self, order):
        """
        Membuat transaksi Midtrans dan mendapatkan Snap Token
        
        Args:
            order: Instance dari model Order
            
        Returns:
            dict: Response dari Midtrans berisi snap_token dan redirect_url
        """
        
        # Persiapkan item details untuk Midtrans
        item_details = []
        for order_item in order.items.all():
            item_details.append({
                'id': str(order_item.product.id),
                'price': int(order_item.product_price),
                'quantity': order_item.quantity,
                'name': order_item.product_name[:50],  # Maksimal 50 karakter
            })
        
        # Tambahkan ongkir sebagai item terpisah
        if order.shipping_cost > 0:
            item_details.append({
                'id': 'SHIPPING',
                'price': int(order.shipping_cost),
                'quantity': 1,
                'name': 'Biaya Pengiriman'
            })
        
        # Persiapkan customer details
        customer_details = {
            'first_name': order.user.first_name or order.shipping_name.split()[0],
            'last_name': order.user.last_name or ' ',
            'email': order.user.email,
            'phone': order.shipping_phone,
            'billing_address': {
                'first_name': order.shipping_name,
                'last_name': ' ',
                'email': order.user.email,
                'phone': order.shipping_phone,
                'address': order.shipping_address[:200],  # Maksimal 200 karakter
                'city': order.shipping_city,
                'postal_code': order.shipping_postal_code or '00000',
                'country_code': 'IDN'
            },
            'shipping_address': {
                'first_name': order.shipping_name,
                'last_name': ' ',
                'email': order.user.email,
                'phone': order.shipping_phone,
                'address': order.shipping_address[:200],
                'city': order.shipping_city,
                'postal_code': order.shipping_postal_code or '00000',
                'country_code': 'IDN'
            }
        }
        
        # Parameter transaksi
        transaction_details = {
            'order_id': order.order_number,
            'gross_amount': int(order.total),
        }
        
        # Gabungkan semua parameter
        param = {
            'transaction_details': transaction_details,
            'item_details': item_details,
            'customer_details': customer_details,
            'enabled_payments': [
                'credit_card', 'bca_va', 'bni_va', 'bri_va', 
                'permata_va', 'other_va', 'gopay', 'shopeepay', 
                'qris', 'cimb_clicks', 'danamon_online'
            ],
            'credit_card': {
                'secure': True,
                'bank': 'bca',
                'installment': {
                    'required': False,
                    'terms': {
                        'bni': [3, 6, 12],
                        'mandiri': [3, 6, 12],
                        'cimb': [3],
                        'bca': [3, 6, 12],
                        'maybank': [3, 6, 12],
                    }
                }
            },
            'callbacks': {
                'finish': f'{settings.ALLOWED_HOSTS[0]}/order-success/{order.id}/'
            }
        }
        
        try:
            # Buat transaksi dan dapatkan snap token
            transaction = self.snap.create_transaction(param)
            
            return {
                'success': True,
                'snap_token': transaction['token'],
                'redirect_url': transaction['redirect_url']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_transaction_status(self, order_id):
        """
        Cek status transaksi dari Midtrans
        
        Args:
            order_id: Order number/ID
            
        Returns:
            dict: Status transaksi dari Midtrans
        """
        try:
            status_response = self.snap.transactions.status(order_id)
            return {
                'success': True,
                'data': status_response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }