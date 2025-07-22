#!/usr/bin/env python3
"""
Manual authentication testing script for SchoolDriver Modern
"""
import requests
from requests.sessions import Session
import time

BASE_URL = "http://localhost:8000"

def test_login_page():
    """Test if login page loads correctly"""
    print("=== Testing Login Page ===")
    try:
        response = requests.get(f"{BASE_URL}/accounts/login/")
        print(f"Status Code: {response.status_code}")
        print(f"Page Title: {response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else 'No title found'}")
        
        # Check for form elements
        has_username = 'name="username"' in response.text or 'id="username"' in response.text
        has_password = 'name="password"' in response.text or 'id="password"' in response.text
        has_remember = 'remember' in response.text.lower()
        has_forgot = 'forgot' in response.text.lower() or 'reset' in response.text.lower()
        
        print(f"Has username field: {has_username}")
        print(f"Has password field: {has_password}")
        print(f"Has remember-me: {has_remember}")
        print(f"Has forgot password: {has_forgot}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error accessing login page: {e}")
        return False

def test_admin_page():
    """Test if admin page loads correctly"""
    print("\n=== Testing Admin Page ===")
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        print(f"Status Code: {response.status_code}")
        print(f"Redirects to login: {'login' in response.url}")
        
        return response.status_code in [200, 302]
    except Exception as e:
        print(f"Error accessing admin page: {e}")
        return False

def test_login_attempt(username, password, should_succeed=False):
    """Test login with given credentials"""
    print(f"\n=== Testing Login: {username} ===")
    
    session = Session()
    
    try:
        # Get login page to extract CSRF token
        login_page = session.get(f"{BASE_URL}/accounts/login/")
        
        # Extract CSRF token
        csrf_token = None
        if 'csrfmiddlewaretoken' in login_page.text:
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        print(f"CSRF Token found: {csrf_token is not None}")
        
        # Attempt login
        login_data = {
            'username': username,
            'password': password,
        }
        
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        response = session.post(f"{BASE_URL}/accounts/login/", data=login_data)
        
        print(f"Login attempt status: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        # Check if login was successful
        success = response.status_code == 302 or 'dashboard' in response.url or response.url != f"{BASE_URL}/accounts/login/"
        print(f"Login successful: {success}")
        
        if success and should_succeed:
            # Test dashboard access
            dashboard_response = session.get(f"{BASE_URL}/")
            print(f"Dashboard access: {dashboard_response.status_code}")
            
        return success
        
    except Exception as e:
        print(f"Error during login attempt: {e}")
        return False

def test_password_reset():
    """Test password reset functionality"""
    print("\n=== Testing Password Reset ===")
    try:
        # Check if password reset page exists
        response = requests.get(f"{BASE_URL}/accounts/password/reset/")
        print(f"Password reset page status: {response.status_code}")
        
        if response.status_code == 200:
            has_email_field = 'email' in response.text.lower()
            print(f"Has email field: {has_email_field}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error accessing password reset: {e}")
        return False

def main():
    print("SchoolDriver Modern Authentication Testing")
    print("=" * 50)
    
    start_time = time.time()
    
    # Test basic page loads
    login_works = test_login_page()
    admin_works = test_admin_page()
    
    # Test login attempts
    admin_success = test_login_attempt("admin", "admin123", should_succeed=True)
    invalid_success = test_login_attempt("invalid", "invalid", should_succeed=False)
    
    # Test password reset
    reset_works = test_password_reset()
    
    # Summary
    print("\n" + "=" * 50)
    print("TESTING SUMMARY")
    print("=" * 50)
    print(f"Login page loads: {'✓' if login_works else '✗'}")
    print(f"Admin page accessible: {'✓' if admin_works else '✗'}")
    print(f"Valid login (admin/admin123): {'✓' if admin_success else '✗'}")
    print(f"Invalid login rejected: {'✓' if not invalid_success else '✗'}")
    print(f"Password reset available: {'✓' if reset_works else '✗'}")
    
    print(f"\nTotal test time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
