#!/usr/bin/env python3
"""
Test admin login directly through Django admin interface.
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Setup Django
sys.path.append('./schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

def test_admin_direct_login():
    """Test admin login directly through /admin/login/."""
    print("🔑 Testing Django admin login directly...")
    
    session = requests.Session()
    
    try:
        # Get admin login page specifically
        admin_login_url = "http://localhost:8001/admin/login/"
        login_page = session.get(admin_login_url)
        
        print(f"📝 Admin login page status: {login_page.status_code}")
        
        if login_page.status_code != 200:
            print(f"❌ Cannot access admin login page")
            return False
            
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        # Try admin login with next parameter
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token,
            'next': '/admin/'
        }
        
        print("📤 Submitting admin login...")
        login_response = session.post(admin_login_url, data=login_data, allow_redirects=False)
        
        print(f"📝 Login response status: {login_response.status_code}")
        print(f"📝 Response headers: {dict(login_response.headers)}")
        
        # Check redirect
        if login_response.status_code == 302:
            location = login_response.headers.get('Location', '')
            print(f"📍 Redirect location: {location}")
            
            if '/admin/' in location:
                print("✅ Success! Redirected to admin")
                
                # Follow redirect to admin
                admin_response = session.get("http://localhost:8001" + location)
                print(f"📝 Admin page status: {admin_response.status_code}")
                
                if admin_response.status_code == 200:
                    # Check if we're actually in admin
                    if 'Django administration' in admin_response.text or 'admin' in admin_response.text.lower():
                        print("✅ Successfully logged into Django admin!")
                        return True
                    else:
                        print("⚠️  Logged in but not in admin interface")
                        return False
                else:
                    print(f"❌ Admin page not accessible (status: {admin_response.status_code})")
                    return False
            else:
                print(f"❌ Wrong redirect location: {location}")
                return False
        else:
            print("❌ No redirect - login failed")
            
            # Check for errors
            if login_response.status_code == 200:
                error_soup = BeautifulSoup(login_response.content, 'html.parser')
                error_elements = error_soup.find_all(['div', 'p'], class_=['errornote', 'error'])
                for error in error_elements:
                    print(f"❌ Error: {error.get_text().strip()}")
            
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_admin_direct_login()
    if success:
        print("\n🎉 Django admin login is working!")
        print("   URL: http://localhost:8001/admin/")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n💥 Django admin login is still broken!")
    
    sys.exit(0 if success else 1)
