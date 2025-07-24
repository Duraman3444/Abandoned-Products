from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using key"""
    return dictionary.get(key)

@register.filter
def add_days(date, days):
    """Add or subtract days from a date"""
    try:
        if isinstance(date, str):
            # If it's a string, try to parse it as a date
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif hasattr(date, 'date'):
            # If it's a datetime, get the date part
            date = date.date()
        
        # Add the specified number of days
        result = date + timedelta(days=int(days))
        return result
    except (ValueError, TypeError, AttributeError):
        return date
