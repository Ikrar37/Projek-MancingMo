from django import template
from datetime import datetime

register = template.Library()

# Dictionary bulan Indonesia
BULAN_INDONESIA = {
    1: 'Januari',
    2: 'Februari', 
    3: 'Maret',
    4: 'April',
    5: 'Mei',
    6: 'Juni',
    7: 'Juli',
    8: 'Agustus',
    9: 'September',
    10: 'Oktober',
    11: 'November',
    12: 'Desember'
}

@register.filter(name='bulan_indonesia')
def bulan_indonesia(value, format_type='F Y'):
    """
    Filter untuk mengubah tanggal ke format Indonesia
    
    Usage:
        {{ user.date_joined|bulan_indonesia }}  -> "Oktober 2025"
        {{ user.date_joined|bulan_indonesia:"d F Y" }}  -> "7 Oktober 2025"
    """
    if not value:
        return ''
    
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except:
            return value
    
    bulan = BULAN_INDONESIA.get(value.month, '')
    
    if format_type == 'F Y':
        return f"{bulan} {value.year}"
    elif format_type == 'd F Y':
        return f"{value.day} {bulan} {value.year}"
    elif format_type == 'F':
        return bulan
    else:
        # Fallback ke format default
        return f"{bulan} {value.year}"