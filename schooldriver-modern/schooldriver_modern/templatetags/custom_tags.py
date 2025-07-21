from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.simple_tag
def get_user_role(user):
    """Get the user's role from their groups"""
    if not user or not user.is_authenticated:
        return "Guest"
    
    if user.groups.exists():
        return user.groups.first().name
    
    return "User"
