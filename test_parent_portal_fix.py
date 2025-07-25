#!/usr/bin/env python3
"""Test the parent portal authentication fix."""

import requests
import time

def test_parent_portal():
    """Test the parent portal with fixed authentication URLs."""
    
    print("🧪 TESTING PARENT PORTAL FIX")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    try:
        # First, get the login page to get CSRF token
        print("🔐 Getting login page...")
        login_page = session.get(f"{base_url}/accounts/login/")
        
        if login_page.status_code != 200:
            print(f"❌ Could not get login page: {login_page.status_code}")
            return
        
        print("✅ Got login page")
        
        # Extract CSRF token
        csrf_token = None
        for line in login_page.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                start = line.find('value="') + 7
                end = line.find('"', start)
                csrf_token = line[start:end]
                break
        
        if not csrf_token:
            print("❌ Could not find CSRF token")
            return
        
        print("✅ Found CSRF token")
        
        # Login with parent account
        print("🔑 Attempting parent login...")
        login_data = {
            'username': 'parent1',
            'password': 'password123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{base_url}/accounts/login/", data=login_data)
        
        if response.status_code == 200 and 'parent' in response.url:
            print("✅ Successfully logged in and redirected to parent portal")
        elif response.status_code == 302:
            print(f"✅ Login redirect: {response.headers.get('Location', 'Unknown')}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response URL: {response.url}")
            return
        
        # Test parent dashboard
        print("\n📊 Testing parent dashboard...")
        dashboard = session.get(f"{base_url}/parent/")
        
        if dashboard.status_code == 200:
            content = dashboard.text
            print("✅ Parent dashboard accessible")
            
            # Check for parent-specific content
            if "Parent Portal" in content or "Dashboard" in content:
                print("✅ Dashboard shows parent portal content")
            else:
                print("⚠️ Dashboard content unclear")
            
            # Check if logout link exists (shouldn't cause template error)
            if "Logout" in content:
                print("✅ Logout link rendered without error")
            else:
                print("⚠️ No logout link found")
                
        else:
            print(f"❌ Could not access parent dashboard: {dashboard.status_code}")
            if dashboard.status_code == 500:
                print("❌ Server error - authentication namespace issue likely persists")
        
        print("\n✅ PARENT PORTAL TESTING COMPLETED")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    # Wait a moment for server to start
    time.sleep(2)
    test_parent_portal()
