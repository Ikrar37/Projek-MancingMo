# products/templatetags/currency_filters.py
from django import template

register = template.Library()

@register.filter
def rupiah(value):
    """
    Format angka menjadi format Rupiah Indonesia dengan titik sebagai pemisah ribuan
    Contoh: 1000000 menjadi 1.000.000
    """
    try:
        value = float(value)
        # Format angka dengan pemisah ribuan menggunakan titik
        formatted = "{:,.0f}".format(value).replace(',', '.')
        return formatted
    except (ValueError, TypeError):
        return value