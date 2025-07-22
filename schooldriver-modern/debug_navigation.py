#!/usr/bin/env python3
"""
Navigation Debug Script
Run this to test direct URL access and identify navigation issues.
"""

import os
import sys
import django

# Setup Django
sys.path.append('schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from schooldriver_modern.roles import get_user_role

def test_navigation_debug():
    """Test navigation URLs and user access"""
    
    print("🔍 NAVIGATION DEBUG STARTED")
    print("=" * 50)
    
    # Test URL generation
    print("\n📍 URL GENERATION TEST:")
    try:
        urls = {
            'dashboard': reverse('student_portal:dashboard'),
            'grades': reverse('student_portal:grades'),
            'schedule': reverse('student_portal:schedule'),
            'attendance': reverse('student_portal:attendance'),
            'profile': reverse('student_portal:profile'),
        }
        
        for name, url in urls.items():
            print(f"✅ {name}: {url}")
            
    except Exception as e:
        print(f"❌ URL Generation Error: {e}")
        return
    
    # Test user authentication
    print("\n👤 USER AUTHENTICATION TEST:")
    try:
        user = User.objects.get(username='test2')
        role = get_user_role(user)
        print(f"✅ User 'test2' exists")
        print(f"✅ User role: {role}")
        print(f"✅ User groups: {[g.name for g in user.groups.all()]}")
        print(f"✅ User active: {user.is_active}")
        
    except User.DoesNotExist:
        print("❌ User 'test2' not found")
        return
    except Exception as e:
        print(f"❌ User test error: {e}")
        return
    
    # Test direct URL access
    print("\n🌐 DIRECT URL ACCESS TEST:")
    client = Client()
    
    # Login the user
    login_success = client.login(username='test2', password='student123')
    print(f"🔐 Login success: {login_success}")
    
    if not login_success:
        print("❌ Cannot proceed - login failed")
        return
    
    # Test each URL
    for name, url in urls.items():
        try:
            response = client.get(url, HTTP_HOST='localhost')
            print(f"🌍 {name} ({url}): Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success - Page loaded")
            elif response.status_code == 302:
                print(f"   🔄 Redirect to: {response.get('Location', 'Unknown')}")
            elif response.status_code == 403:
                print(f"   ❌ Forbidden - Permission denied")
            elif response.status_code == 404:
                print(f"   ❌ Not Found - URL doesn't exist")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name} ({url}): Error - {e}")
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG COMPLETE")

if __name__ == "__main__":
    test_navigation_debug()
