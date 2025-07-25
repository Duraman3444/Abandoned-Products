#!/usr/bin/env python3
"""Manual test of authentication URL resolution."""

import os
import sys
import django

# Add the Django app directory to the Python path
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.urls import reverse
from django.test import RequestFactory
from django.contrib.auth.models import User

def test_url_resolution():
    """Test URL resolution for authentication URLs."""
    
    print("🔍 TESTING URL RESOLUTION")
    print("=" * 40)
    
    try:
        # Test logout URL
        logout_url = reverse('logout')
        print(f"✅ logout URL resolves to: {logout_url}")
    except Exception as e:
        print(f"❌ logout URL failed: {e}")
    
    try:
        # Test login URL  
        login_url = reverse('login')
        print(f"✅ login URL resolves to: {login_url}")
    except Exception as e:
        print(f"❌ login URL failed: {e}")
    
    try:
        # Test parent portal URLs
        parent_dashboard = reverse('parent_portal:dashboard')
        print(f"✅ parent_portal:dashboard URL resolves to: {parent_dashboard}")
    except Exception as e:
        print(f"❌ parent_portal:dashboard URL failed: {e}")
    
    # Test if we can render a basic parent template
    from django.template import Template, Context
    from django.template.loader import get_template
    
    try:
        # Create a mock request and user
        factory = RequestFactory()
        request = factory.get('/parent/')
        user = User.objects.filter(username='parent1').first()
        if user:
            request.user = user
            print(f"✅ Found parent1 user: {user.get_full_name()}")
        else:
            print("❌ parent1 user not found")
            return
        
        # Test template rendering
        template_content = """
        {% load static %}
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
        <a href="{% url 'logout' %}">Logout</a>
        <a href="{% url 'login' %}">Login</a>
        </body>
        </html>
        """
        
        template = Template(template_content)
        context = Context({'user': user, 'request': request})
        rendered = template.render(context)
        
        if 'logout' in rendered and 'login' in rendered:
            print("✅ Template renders authentication URLs successfully")
        else:
            print("❌ Template rendering failed")
            
    except Exception as e:
        print(f"❌ Template test failed: {e}")

if __name__ == '__main__':
    test_url_resolution()
