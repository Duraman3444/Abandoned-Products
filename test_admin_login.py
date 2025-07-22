#!/usr/bin/env python3
"""
Test admin login with the new credentials.
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

def test_admin_login():
    """Test admin login with username=admin, password=admin123."""
    print("🔑 Testing admin login...")
    
    session = requests.Session()
    
    try:
        # Get login page
        login_url = "http://localhost:8001/admin/login/"
        login_page = session.get(login_url)
        
        if login_page.status_code != 200:
            print(f"❌ Cannot access login page (status: {login_page.status_code})")
            return False
            
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        # Attempt login
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token,
        }
        
        login_response = session.post(login_url, data=login_data, allow_redirects=False)
        
        print(f"📝 Login response status: {login_response.status_code}")
        print(f"📝 Login response headers: {dict(login_response.headers)}")
        
        # Check if redirect to admin (successful login)
        if login_response.status_code == 302:
            location = login_response.headers.get('Location', '')
            if '/admin/' in location:
                print("✅ Login successful! Redirected to admin panel")
                
                # Test dashboard access
                dashboard_response = session.get("http://localhost:8001/dashboard/")
                if dashboard_response.status_code == 200:
                    print("✅ Dashboard accessible after login")
                    return True
                else:
                    print(f"⚠️  Dashboard access failed (status: {dashboard_response.status_code})")
                    return False
            else:
                print(f"❌ Login failed - redirected to: {location}")
                return False
        else:
            print("❌ Login failed - no redirect")
            
            # Check for error messages
            if login_response.status_code == 200:
                error_soup = BeautifulSoup(login_response.content, 'html.parser')
                error_msg = error_soup.find('p', class_='errornote')
                if error_msg:
                    print(f"❌ Error message: {error_msg.get_text().strip()}")
            
            return False
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_admin_login()
    if success:
        print("\n🎉 Admin login is working!")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n💥 Admin login is still broken!")
    
    sys.exit(0 if success else 1)
