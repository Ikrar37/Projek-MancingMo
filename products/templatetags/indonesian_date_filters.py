# products/templatetags/indonesian_date_filters.py
from django import template
from django.utils import timezone
import datetime
from datetime import date

register = template.Library()

@register.filter
def bulan_indonesia(value):
    """
    Convert datetime/date to Indonesian month format
    Example: 2025-11-13 → 13 November 2025
    """
    if not value:
        return ""
    
    # Handle string dates
    if isinstance(value, str):
        # Coba berbagai format date
        formats = [
            '%Y-%m-%d %H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S%z', 
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                if 'T' in value:
                    # Handle ISO format
                    value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.datetime.strptime(value, fmt)
                break
            except (ValueError, TypeError):
                continue
        else:
            # Jika semua format gagal, return original value
            return value
    
    # Dictionary untuk nama bulan dalam Bahasa Indonesia
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    
    try:
        # Handle date objects (tanpa time)
        if isinstance(value, date) and not isinstance(value, datetime.datetime):
            return f"{value.day} {bulan[value.month]} {value.year}"
        
        # Handle datetime objects
        return f"{value.day} {bulan[value.month]} {value.year}"
        
    except (AttributeError, KeyError, ValueError):
        # Jika ada error, return string representation
        return str(value)

@register.filter
def tanggal_indonesia(value):
    """
    Convert datetime to Indonesian date format with time
    Example: 2025-11-13 02:19:09 → 13 November 2025, 02:19
    """
    if not value:
        return ""
    
    # Handle string dates
    if isinstance(value, str):
        formats = [
            '%Y-%m-%d %H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S%z', 
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                if 'T' in value:
                    value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.datetime.strptime(value, fmt)
                break
            except (ValueError, TypeError):
                continue
        else:
            return value
    
    # ✅ PERBAIKAN: Konversi ke timezone Asia/Makassar sesuai settings
    if isinstance(value, datetime.datetime) and timezone.is_aware(value):
        value = timezone.localtime(value)  # Ini akan menggunakan TIME_ZONE dari settings
    
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    
    try:
        # Handle date objects
        if isinstance(value, date) and not isinstance(value, datetime.datetime):
            return f"{value.day} {bulan[value.month]} {value.year}"
        
        # Handle datetime objects with time
        return f"{value.day} {bulan[value.month]} {value.year}, {value.strftime('%H:%M')}"
        
    except (AttributeError, KeyError, ValueError):
        return str(value)

@register.filter
def format_rupiah(value):
    """
    Format number to Rupiah currency format
    Example: 100000 → Rp 100.000
    """
    if value is None:
        return "Rp 0"
    
    try:
        value = float(value)
        return f"Rp {value:,.0f}".replace(',', '.')
    except (ValueError, TypeError):
        return f"Rp {value}"

@register.filter
def nama_bulan(value):
    """
    Get Indonesian month name from month number (1-12)
    """
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    return bulan.get(value, '')

@register.filter
def tanggal_singkat(value):
    """
    Short Indonesian date format: 13 Nov 2025
    """
    if not value:
        return ""
    
    # Handle string dates
    if isinstance(value, str):
        formats = [
            '%Y-%m-%d %H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S%z', 
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                if 'T' in value:
                    value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.datetime.strptime(value, fmt)
                break
            except (ValueError, TypeError):
                continue
        else:
            return value
    
    # ✅ PERBAIKAN: Konversi ke timezone Asia/Makassar sesuai settings
    if isinstance(value, datetime.datetime) and timezone.is_aware(value):
        value = timezone.localtime(value)  # Ini akan menggunakan TIME_ZONE dari settings
    
    bulan_singkat = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
        9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
    }
    
    try:
        if isinstance(value, date) and not isinstance(value, datetime.datetime):
            return f"{value.day} {bulan_singkat[value.month]} {value.year}"
        
        return f"{value.day} {bulan_singkat[value.month]} {value.year}"
        
    except (AttributeError, KeyError, ValueError):
        return str(value)