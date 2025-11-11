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
        
        try:
            print(f"🔢 MEMBUAT TRANSAKSI MIDTRANS UNTUK ORDER: {order.order_number}")
            
            # ✅ HITUNG ULANG DENGAN PASTI - INI YANG PERLU DIPERBAIKI
            item_details = []
            gross_amount = 0
            
            # 1. PRODUK-PRODUK
            for order_item in order.items.all():
                product_price = int(order_item.product_price)
                product_total = product_price * order_item.quantity
                
                item_details.append({
                    'id': str(order_item.product.id),
                    'price': product_price,
                    'quantity': order_item.quantity,
                    'name': order_item.product_name[:50]
                })
                gross_amount += product_total
                print(f"   📦 {order_item.product_name}: {product_price} x {order_item.quantity} = {product_total}")

            # 2. BIAYA PENGIRIMAN
            shipping_cost = int(order.shipping_cost)
            if shipping_cost > 0:
                item_details.append({
                    'id': 'shipping',
                    'price': shipping_cost,
                    'quantity': 1,
                    'name': 'Biaya Pengiriman'
                })
                gross_amount += shipping_cost
                print(f"   🚚 Biaya Pengiriman: {shipping_cost}")

            # 3. DISKON VOUCHER (JIKA ADA) - ✅ INI YANG DITAMBAHKAN
            voucher_discount = int(order.voucher_discount)
            if voucher_discount > 0:
                item_details.append({
                    'id': 'voucher',
                    'price': -voucher_discount,  # HARUS NEGATIVE
                    'quantity': 1,
                    'name': f'Diskon Voucher {order.voucher_code}' if order.voucher_code else 'Diskon Voucher'
                })
                gross_amount -= voucher_discount
                print(f"   💰 Diskon Voucher: -{voucher_discount}")

            # ✅ PASTIKAN GROSS AMOUNT SAMA DENGAN ORDER TOTAL
            calculated_total = gross_amount
            order_total = int(order.total)
            
            print(f"   🧮 TOTAL PERHITUNGAN: {calculated_total}")
            print(f"   🧮 TOTAL DI ORDER: {order_total}")
            
            # JIKA BERBEDA, PAKAI YANG DI ORDER
            if calculated_total != order_total:
                print(f"   ⚠️  PERHITUNGAN BERBEDA! Adjusting...")
                gross_amount = order_total

            print(f"   ✅ FINAL GROSS AMOUNT: {gross_amount}")

            # ✅ SNAP PARAMETERS
            snap_param = {
                'transaction_details': {
                    'order_id': order.order_number,
                    'gross_amount': gross_amount
                },
                'item_details': item_details,
                'customer_details': {
                    'first_name': order.shipping_name.split(' ')[0],
                    'last_name': ' '.join(order.shipping_name.split(' ')[1:]) if len(order.shipping_name.split(' ')) > 1 else '',
                    'email': order.user.email,
                    'phone': order.shipping_phone,
                    'billing_address': {
                        'first_name': order.shipping_name.split(' ')[0],
                        'last_name': ' '.join(order.shipping_name.split(' ')[1:]) if len(order.shipping_name.split(' ')) > 1 else '',
                        'email': order.user.email,
                        'phone': order.shipping_phone,
                        'address': order.shipping_address[:200],
                        'city': order.shipping_city,
                        'postal_code': order.shipping_postal_code or '00000',
                        'country_code': 'IDN'
                    },
                    'shipping_address': {
                        'first_name': order.shipping_name.split(' ')[0],
                        'last_name': ' '.join(order.shipping_name.split(' ')[1:]) if len(order.shipping_name.split(' ')) > 1 else '',
                        'email': order.user.email,
                        'phone': order.shipping_phone,
                        'address': order.shipping_address[:200],
                        'city': order.shipping_city,
                        'postal_code': order.shipping_postal_code or '00000',
                        'country_code': 'IDN'
                    }
                },
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
                    'finish': f'{settings.ALLOWED_HOSTS[0]}/order-success/{order.id}/' if settings.ALLOWED_HOSTS else f'http://localhost:8000/order-success/{order.id}/'
                }
            }

            print(f"   📦 Snap Parameters siap, membuat token...")
            
            # CREATE SNAP TOKEN
            transaction = self.snap.create_transaction(snap_param)
            snap_token = transaction['token']
            
            print(f"   ✅ Snap token berhasil: {snap_token[:50]}...")
            
            return {
                'success': True,
                'snap_token': snap_token,
                'redirect_url': transaction.get('redirect_url', '')
            }

        except Exception as e:
            print(f"   ❌ Error Midtrans: {str(e)}")
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