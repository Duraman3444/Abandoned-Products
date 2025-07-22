#!/usr/bin/env python3
"""
Simple test to check browser console for chart initialization messages.
"""
import os
import sys
import django
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# Setup Django
sys.path.append('./schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

def test_console_logs():
    """Test chart initialization via console logs."""
    print("🔍 Testing chart initialization console logs...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Login
        driver.get("http://localhost:8001/admin/login/")
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        username_field.send_keys("admin")
        password_field.send_keys("admin")
        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        
        # Go to dashboard
        driver.get("http://localhost:8001/dashboard/")
        
        # Wait for page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "charts-grid"))
        )
        
        # Wait for initialization
        time.sleep(8)
        
        # Get console logs
        logs = driver.get_log('browser')
        
        print("\n📝 Console Logs Analysis:")
        
        # Check for success indicators
        success_patterns = [
            "Chart.js loaded",
            "Canvas Pipeline Progress found",
            "Canvas Document Completion found", 
            "Canvas Status Distribution found",
            "Canvas Monthly Trends found",
            "Pipeline Progress chart created",
            "Document Completion chart created",
            "Status Distribution chart created",
            "Monthly Trends chart created",
            "ALL 4 CHARTS INITIALIZATION COMPLETED"
        ]
        
        found_patterns = []
        errors = []
        
        for log in logs:
            message = log['message']
            level = log['level']
            
            if level == 'SEVERE':
                errors.append(message)
            
            for pattern in success_patterns:
                if pattern in message:
                    found_patterns.append(pattern)
                    print(f"✅ Found: {pattern}")
        
        print(f"\n📊 Results:")
        print(f"   Success patterns found: {len(found_patterns)}/{len(success_patterns)}")
        print(f"   Errors: {len(errors)}")
        
        if errors:
            print("\n❌ Errors found:")
            for error in errors:
                if 'favicon' not in error:  # Ignore favicon 404
                    print(f"   {error}")
        
        # Check specific success
        if "ALL 4 CHARTS INITIALIZATION COMPLETED" in str(logs):
            print("\n🎉 SUCCESS: All charts initialized!")
            return True
        else:
            print("\n💥 FAILURE: Charts not fully initialized")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_console_logs()
    sys.exit(0 if success else 1)
