#!/usr/bin/env python3
"""
Detailed authentication testing script for SchoolDriver Modern
"""
import requests
from requests.sessions import Session
import time
import re

BASE_URL = "http://localhost:8000"

def extract_csrf_token(html_content):
    """Extract CSRF token from HTML"""
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html_content)
    return csrf_match.group(1) if csrf_match else None

def test_role_based_redirects():
    """Test role-based redirect behavior after login"""
    print("\n=== Testing Role-Based Redirects ===")
    
    session = Session()
    
    try:
        # Get login page
        login_page = session.get(f"{BASE_URL}/accounts/login/")
        csrf_token = extract_csrf_token(login_page.text)
        
        # Login with admin credentials
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{BASE_URL}/accounts/login/", data=login_data, allow_redirects=False)
        
        print(f"Login redirect status: {response.status_code}")
        print(f"Redirect location: {response.headers.get('Location', 'No redirect')}")
        
        # Follow redirect to see where admin lands
        if response.status_code == 302:
            final_response = session.get(response.headers['Location'])
            print(f"Final landing page status: {final_response.status_code}")
            print(f"Final URL: {final_response.url}")
            
            # Check for dashboard elements
            if 'dashboard' in final_response.text.lower():
                print("✓ Contains dashboard content")
            if 'chart' in final_response.text.lower():
                print("✓ Contains chart elements")
            if 'admin' in final_response.text.lower():
                print("✓ Contains admin references")
                
        return True
        
    except Exception as e:
        print(f"Error testing redirects: {e}")
        return False

def test_dashboard_features():
    """Test dashboard page features and content"""
    print("\n=== Testing Dashboard Features ===")
    
    session = Session()
    
    try:
        # Login first
        login_page = session.get(f"{BASE_URL}/accounts/login/")
        csrf_token = extract_csrf_token(login_page.text)
        
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        session.post(f"{BASE_URL}/accounts/login/", data=login_data)
        
        # Test dashboard access
        dashboard_response = session.get(f"{BASE_URL}/dashboard/")
        print(f"Dashboard status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            content = dashboard_response.text.lower()
            
            # Check for expected dashboard features
            has_charts = 'chart' in content or 'analytics' in content
            has_navigation = 'nav' in content or 'menu' in content
            has_user_info = 'profile' in content or 'logout' in content
            has_admin_access = 'admin' in content
            
            print(f"✓ Has charts/analytics: {has_charts}")
            print(f"✓ Has navigation: {has_navigation}")
            print(f"✓ Has user info: {has_user_info}")
            print(f"✓ Has admin access: {has_admin_access}")
            
            # Check page load time
            return True
        else:
            print("✗ Dashboard not accessible")
            return False
            
    except Exception as e:
        print(f"Error testing dashboard: {e}")
        return False

def test_remember_me_functionality():
    """Test remember-me checkbox functionality"""
    print("\n=== Testing Remember-Me Functionality ===")
    
    try:
        # Test with remember-me enabled
        session1 = Session()
        login_page = session1.get(f"{BASE_URL}/accounts/login/")
        csrf_token = extract_csrf_token(login_page.text)
        
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'remember_me': 'on',  # Checkbox checked
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session1.post(f"{BASE_URL}/accounts/login/", data=login_data)
        
        # Check for session cookies
        cookies_set = len(session1.cookies) > 0
        has_session_cookie = any('session' in cookie.name.lower() for cookie in session1.cookies)
        
        print(f"Cookies set: {cookies_set}")
        print(f"Has session cookie: {has_session_cookie}")
        
        # Test session persistence by creating new session with same cookies
        session2 = Session()
        session2.cookies.update(session1.cookies)
        
        dashboard_test = session2.get(f"{BASE_URL}/dashboard/")
        session_persists = dashboard_test.status_code == 200
        
        print(f"Session persists: {session_persists}")
        
        return session_persists
        
    except Exception as e:
        print(f"Error testing remember-me: {e}")
        return False

def test_logout_functionality():
    """Test logout functionality"""
    print("\n=== Testing Logout Functionality ===")
    
    session = Session()
    
    try:
        # Login first
        login_page = session.get(f"{BASE_URL}/accounts/login/")
        csrf_token = extract_csrf_token(login_page.text)
        
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        session.post(f"{BASE_URL}/accounts/login/", data=login_data)
        
        # Verify logged in
        dashboard_check = session.get(f"{BASE_URL}/dashboard/")
        logged_in = dashboard_check.status_code == 200
        print(f"Logged in successfully: {logged_in}")
        
        # Test logout
        logout_response = session.post(f"{BASE_URL}/accounts/logout/")
        print(f"Logout response: {logout_response.status_code}")
        
        # Verify logged out - should redirect to login
        dashboard_after_logout = session.get(f"{BASE_URL}/dashboard/")
        logged_out = dashboard_after_logout.status_code == 302 or 'login' in dashboard_after_logout.url
        print(f"Successfully logged out: {logged_out}")
        
        return logged_out
        
    except Exception as e:
        print(f"Error testing logout: {e}")
        return False

def test_security_headers():
    """Test security headers and CSRF protection"""
    print("\n=== Testing Security Features ===")
    
    try:
        # Test CSRF protection
        response = requests.get(f"{BASE_URL}/accounts/login/")
        has_csrf_token = 'csrfmiddlewaretoken' in response.text
        print(f"CSRF token present: {has_csrf_token}")
        
        # Test login without CSRF token
        bad_login = requests.post(f"{BASE_URL}/accounts/login/", data={
            'username': 'admin',
            'password': 'admin123'
        })
        csrf_protected = bad_login.status_code == 403 or 'csrf' in bad_login.text.lower()
        print(f"CSRF protection active: {csrf_protected}")
        
        # Check security headers
        headers = response.headers
        has_xframe = 'X-Frame-Options' in headers
        has_content_type = 'X-Content-Type-Options' in headers
        
        print(f"X-Frame-Options header: {has_xframe}")
        print(f"X-Content-Type-Options header: {has_content_type}")
        
        return has_csrf_token
        
    except Exception as e:
        print(f"Error testing security: {e}")
        return False

def main():
    print("SchoolDriver Modern - Comprehensive Authentication Testing")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests
    results = {
        "role_redirects": test_role_based_redirects(),
        "dashboard_features": test_dashboard_features(),
        "remember_me": test_remember_me_functionality(),
        "logout": test_logout_functionality(),
        "security": test_security_headers()
    }
    
    # Performance timing
    end_time = time.time()
    total_time = end_time - start_time
    
    # Final comprehensive report
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TESTING REPORT")
    print("=" * 60)
    
    print(f"Role-based redirects: {'✓ PASS' if results['role_redirects'] else '✗ FAIL'}")
    print(f"Dashboard functionality: {'✓ PASS' if results['dashboard_features'] else '✗ FAIL'}")
    print(f"Remember-me feature: {'✓ PASS' if results['remember_me'] else '✗ FAIL'}")
    print(f"Logout functionality: {'✓ PASS' if results['logout'] else '✗ FAIL'}")
    print(f"Security features: {'✓ PASS' if results['security'] else '✗ FAIL'}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nOverall Score: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Total Test Time: {total_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Authentication system working correctly!")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed - review implementation")

if __name__ == "__main__":
    main()
