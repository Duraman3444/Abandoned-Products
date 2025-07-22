#!/usr/bin/env python3
"""
Test script to verify dashboard charts are working correctly.
"""
import os
import sys
import django
import requests
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

def test_dashboard_charts():
    """Test that all 4 dashboard charts are rendered correctly."""
    print("🧪 Testing Dashboard Charts...")
    
    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to dashboard
        print("📍 Navigating to dashboard...")
        driver.get("http://localhost:8001/admin/login/")
        
        # Login
        print("🔐 Logging in...")
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        username_field.send_keys("admin")
        password_field.send_keys("admin")
        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        
        # Navigate to dashboard
        driver.get("http://localhost:8001/dashboard/")
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "charts-grid"))
        )
        
        # Wait a bit more for charts to initialize
        time.sleep(3)
        
        # Check for canvas elements
        chart_ids = ['pipelineChart', 'documentsChart', 'statusChart', 'trendsChart']
        chart_names = ['Pipeline Progress', 'Document Completion', 'Status Distribution', 'Monthly Trends']
        
        print("\n📊 Checking chart canvas elements...")
        charts_found = 0
        
        for chart_id, chart_name in zip(chart_ids, chart_names):
            try:
                canvas = driver.find_element(By.ID, chart_id)
                if canvas:
                    charts_found += 1
                    print(f"✅ {chart_name} canvas found")
                    
                    # Check if canvas has content (width/height > 0)
                    canvas_size = canvas.size
                    if canvas_size['width'] > 0 and canvas_size['height'] > 0:
                        print(f"   📏 Canvas size: {canvas_size['width']}x{canvas_size['height']}")
                    else:
                        print(f"   ⚠️  Canvas has zero dimensions")
                        
            except Exception as e:
                print(f"❌ {chart_name} canvas not found: {e}")
        
        # Check JavaScript console for errors
        print("\n🔍 Checking browser console...")
        logs = driver.get_log('browser')
        error_count = 0
        
        for log in logs:
            if log['level'] == 'SEVERE':
                error_count += 1
                print(f"❌ JS Error: {log['message']}")
            elif 'chart' in log['message'].lower():
                print(f"📝 Chart-related log: {log['message']}")
        
        # Check for chart initialization messages
        success_logs = [log for log in logs if 'Dashboard initialized' in log['message']]
        if success_logs:
            print("✅ Dashboard initialization message found")
        else:
            print("⚠️  Dashboard initialization message not found")
        
        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"   Charts found: {charts_found}/4")
        print(f"   JavaScript errors: {error_count}")
        
        if charts_found == 4 and error_count == 0:
            print("🎉 ALL CHARTS ARE WORKING!")
            return True
        else:
            print("💥 SOME CHARTS ARE BROKEN!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    success = test_dashboard_charts()
    sys.exit(0 if success else 1)
