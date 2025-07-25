#!/usr/bin/env python3
"""Test the fixed student portal with real data."""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.safari.options import Options as SafariOptions

def test_student_portal():
    """Test the student portal with Emma Smith's account."""
    
    print("🧪 TESTING STUDENT PORTAL WITH REAL DATA")
    print("=" * 50)
    
    # Setup Safari driver (best for macOS)
    safari_options = SafariOptions()
    driver = webdriver.Safari(options=safari_options)
    driver.implicitly_wait(10)
    
    try:
        # Test login
        print("🔐 Testing login...")
        driver.get("http://localhost:8000/auth/login/")
        
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("student1")
        password_field.send_keys("password123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        time.sleep(2)
        
        # Check if we're logged in and redirected to student portal
        current_url = driver.current_url
        print(f"📍 Current URL after login: {current_url}")
        
        if "student" in current_url:
            print("✅ Successfully logged in to student portal")
        else:
            print("❌ Login failed or not redirected to student portal")
            return
        
        # Test Dashboard
        print("\n📊 Testing Dashboard...")
        dashboard_content = driver.find_element(By.TAG_NAME, "body").text
        
        if "Emma" in dashboard_content:
            print("✅ Dashboard shows Emma's name")
        else:
            print("❌ Dashboard doesn't show Emma's name")
        
        if "Lisa Garcia" in dashboard_content:
            print("✅ Dashboard shows Lisa Garcia (teacher)")
        else:
            print("❌ Dashboard doesn't show Lisa Garcia")
        
        # Check for courses
        if "English Literature" in dashboard_content:
            print("✅ Dashboard shows English Literature course")
        else:
            print("❌ Dashboard doesn't show English Literature course")
        
        # Test Grades page
        print("\n📈 Testing Grades page...")
        grades_link = driver.find_element(By.LINK_TEXT, "Grades")
        grades_link.click()
        time.sleep(2)
        
        grades_content = driver.find_element(By.TAG_NAME, "body").text
        
        if "No Courses Found" in grades_content:
            print("❌ Grades page still shows 'No Courses Found'")
        elif "English Literature" in grades_content:
            print("✅ Grades page shows English Literature course")
        else:
            print("⚠️ Grades page shows different content")
        
        # Test Assignments page
        print("\n📝 Testing Assignments page...")
        assignments_link = driver.find_element(By.LINK_TEXT, "Assignments")
        assignments_link.click()
        time.sleep(2)
        
        assignments_content = driver.find_element(By.TAG_NAME, "body").text
        
        if "No assignments found" in assignments_content:
            print("❌ Assignments page still shows 'No assignments found'")
        elif "Essay" in assignments_content or "Character Analysis" in assignments_content:
            print("✅ Assignments page shows real assignments")
        else:
            print("⚠️ Assignments page shows different content")
        
        # Test Schedule page
        print("\n📅 Testing Schedule page...")
        schedule_link = driver.find_element(By.LINK_TEXT, "Schedule")
        schedule_link.click()
        time.sleep(2)
        
        schedule_content = driver.find_element(By.TAG_NAME, "body").text
        
        if "Mathematics" in schedule_content and "Algebra II" in schedule_content:
            print("❌ Schedule page still shows hardcoded Mathematics content")
        elif "English Literature" in schedule_content:
            print("✅ Schedule page shows dynamic English Literature content")
        elif "No schedule data available" in schedule_content:
            print("⚠️ Schedule page shows no data message")
        else:
            print("⚠️ Schedule page shows different content")
        
        # Test Attendance page
        print("\n📋 Testing Attendance page...")
        attendance_link = driver.find_element(By.LINK_TEXT, "Attendance")
        attendance_link.click()
        time.sleep(2)
        
        attendance_content = driver.find_element(By.TAG_NAME, "body").text
        
        if "Present" in attendance_content and "Absent" in attendance_content:
            print("✅ Attendance page shows attendance records")
        else:
            print("❌ Attendance page doesn't show proper records")
        
        print(f"\n📸 Final URL: {driver.current_url}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        print("\n🏁 Test completed")
        driver.quit()

if __name__ == "__main__":
    # Wait a moment for server to start
    time.sleep(3)
    test_student_portal()
