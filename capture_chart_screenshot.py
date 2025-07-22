#!/usr/bin/env python3
"""
Capture a screenshot of the dashboard to visually verify charts are working.
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

def capture_dashboard():
    """Capture screenshot of dashboard."""
    print("📸 Capturing dashboard screenshot...")
    
    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate and login
        driver.get("http://localhost:8001/admin/login/")
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        username_field.send_keys("admin")
        password_field.send_keys("admin")
        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        
        # Go to dashboard
        driver.get("http://localhost:8001/dashboard/")
        
        # Wait for charts
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "charts-grid"))
        )
        
        # Wait for chart initialization
        time.sleep(5)
        
        # Capture screenshot
        driver.save_screenshot("dashboard_charts_test.png")
        print("✅ Screenshot saved as dashboard_charts_test.png")
        
        # Get console logs
        logs = driver.get_log('browser')
        print("\n📝 Console logs:")
        for log in logs:
            if 'chart' in log['message'].lower() or 'error' in log['level'].lower():
                print(f"   {log['level']}: {log['message']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    capture_dashboard()
