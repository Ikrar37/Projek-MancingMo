from django import template
from django.utils import timezone
import datetime

register = template.Library()

@register.filter
def indonesian_date(value):
    """
    Convert datetime to Indonesian date format
    Example: "13 November 2025"
    """
    if not value:
        return ""
    
    # Ensure it's a timezone-aware datetime
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    # Indonesian month names
    months = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = value.day
    month = months[value.month - 1]
    year = value.year
    
    return f"{day} {month} {year}"

@register.filter
def indonesian_datetime(value):
    """
    Convert datetime to Indonesian datetime format
    Example: "13 November 2025, 14:30 WITA"
    """
    if not value:
        return ""
    
    # Ensure it's a timezone-aware datetime
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    # Indonesian month names
    months = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = value.day
    month = months[value.month - 1]
    year = value.year
    hour = value.hour
    minute = value.minute
    
    # Format time
    time_str = f"{hour:02d}:{minute:02d}"
    
    return f"{day} {month} {year}, {time_str} WITA"

@register.filter
def indonesian_currency(value):
    """
    Format number to Indonesian currency format
    Example: "Rp 1.000.000"
    """
    if value is None:
        return "Rp 0"
    
    try:
        value = int(value)
        return f"Rp {value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"