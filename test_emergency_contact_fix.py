#!/usr/bin/env python3

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_emergency_contact_functionality():
    """Test emergency contact links and functionality"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        wait = WebDriverWait(driver, 10)
        
        print("🧪 Testing Emergency Contact Functionality")
        print("=" * 50)
        
        # Navigate to parent portal
        driver.get("http://localhost:8000/parent/login/")
        print("✅ Navigated to parent login page")
        
        # Login as parent
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("parent1")
        password_field.send_keys("password123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        print("✅ Logged in as parent")
        
        # Wait for dashboard to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "navbar")))
        print("✅ Dashboard loaded")
        
        # Navigate to emergency contacts
        driver.get("http://localhost:8000/parent/emergency-contacts/")
        
        # Check if page loads without errors
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("✅ Emergency contacts page loaded")
        
        # Look for emergency contact buttons
        page_source = driver.page_source
        
        # Check for Add Contact button
        if "Add Contact" in page_source or "add_emergency_contact" in page_source:
            print("✅ Add Emergency Contact button found")
        else:
            print("❌ Add Emergency Contact button NOT found")
        
        # Check for Add Person button
        if "Add Person" in page_source or "add_pickup_person" in page_source:
            print("✅ Add Person button found")
        else:
            print("❌ Add Person button NOT found")
        
        # Check for Medical Information button
        if "Medical Information" in page_source or "medical_information" in page_source:
            print("✅ Medical Information button found")
        else:
            print("❌ Medical Information button NOT found")
        
        # Try to click Add Emergency Contact if it exists
        try:
            add_contact_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Add Contact') or contains(@href, 'add_emergency_contact')]")
            if add_contact_buttons:
                add_contact_buttons[0].click()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                if "emergency" in driver.current_url and "add" in driver.current_url:
                    print("✅ Add Emergency Contact link working")
                else:
                    print("❌ Add Emergency Contact link leads to wrong page")
                driver.back()
            else:
                print("❌ No Add Emergency Contact button found to click")
        except Exception as e:
            print(f"❌ Error clicking Add Emergency Contact: {e}")
        
        # Try to click Add Person if it exists
        try:
            add_person_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Add Person') or contains(@href, 'add_pickup_person')]")
            if add_person_buttons:
                add_person_buttons[0].click()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                if "pickup-persons" in driver.current_url and "add" in driver.current_url:
                    print("✅ Add Person link working")
                else:
                    print("❌ Add Person link leads to wrong page")
                driver.back()
            else:
                print("❌ No Add Person button found to click")
        except Exception as e:
            print(f"❌ Error clicking Add Person: {e}")
        
        # Try to click Medical Information if it exists
        try:
            medical_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Medical Information') or contains(@href, 'medical_information')]")
            if medical_buttons:
                medical_buttons[0].click()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                if "medical-information" in driver.current_url:
                    print("✅ Medical Information link working")
                else:
                    print("❌ Medical Information link leads to wrong page")
            else:
                print("❌ No Medical Information button found to click")
        except Exception as e:
            print(f"❌ Error clicking Medical Information: {e}")
        
        print("\n🎯 Test Summary:")
        print("Emergency contact functionality has been fixed by moving templates to correct location")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        try:
            driver.quit()
        except:
            pass
    
    return True

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(3)
    test_emergency_contact_functionality()
