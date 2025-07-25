#!/usr/bin/env python3
"""Simple test of the student portal using requests."""

import requests
import time

def test_student_portal():
    """Test the student portal with a simple HTTP request."""
    
    print("🧪 TESTING STUDENT PORTAL WITH SIMPLE HTTP REQUESTS")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    try:
        # First, get the login page to get CSRF token
        print("🔐 Getting login page...")
        login_page = session.get(f"{base_url}/auth/login/")
        
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
        
        # Login
        print("🔑 Attempting login...")
        login_data = {
            'username': 'student1',
            'password': 'password123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{base_url}/auth/login/", data=login_data)
        
        if response.status_code == 200 and 'student' in response.url:
            print("✅ Successfully logged in and redirected to student portal")
        elif response.status_code == 302:
            print(f"✅ Login redirect: {response.headers.get('Location', 'Unknown')}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response URL: {response.url}")
            return
        
        # Test student dashboard
        print("\n📊 Testing student dashboard...")
        dashboard = session.get(f"{base_url}/student/")
        
        if dashboard.status_code == 200:
            content = dashboard.text
            print("✅ Student dashboard accessible")
            
            # Check for Emma's data
            if "Emma" in content:
                print("✅ Dashboard shows Emma's name")
            else:
                print("❌ Dashboard doesn't show Emma's name")
            
            if "English Literature" in content:
                print("✅ Dashboard shows English Literature course")
            else:
                print("❌ Dashboard doesn't show English Literature course")
            
            if "Lisa Garcia" in content:
                print("✅ Dashboard shows Lisa Garcia as teacher")
            else:
                print("❌ Dashboard doesn't show Lisa Garcia")
                
            # Check GPA
            if "0.0" in content and "Current GPA" in content:
                print("⚠️ GPA is still 0.0 (may need grade calculation)")
            elif "3." in content or "4." in content:
                print("✅ Dashboard shows calculated GPA")
            
        else:
            print(f"❌ Could not access dashboard: {dashboard.status_code}")
        
        # Test grades page
        print("\n📈 Testing grades page...")
        grades = session.get(f"{base_url}/student/grades/")
        
        if grades.status_code == 200:
            content = grades.text
            print("✅ Grades page accessible")
            
            if "No Courses Found" in content:
                print("❌ Grades page still shows 'No Courses Found'")
            elif "English Literature" in content:
                print("✅ Grades page shows English Literature")
            else:
                print("⚠️ Grades page content unclear")
        else:
            print(f"❌ Could not access grades page: {grades.status_code}")
        
        # Test assignments page
        print("\n📝 Testing assignments page...")
        assignments = session.get(f"{base_url}/student/assignments/")
        
        if assignments.status_code == 200:
            content = assignments.text
            print("✅ Assignments page accessible")
            
            if "No assignments found" in content:
                print("❌ Assignments page still shows 'No assignments found'")
            elif "Essay" in content or "Character Analysis" in content:
                print("✅ Assignments page shows real assignments")
            else:
                print("⚠️ Assignments page content unclear")
        else:
            print(f"❌ Could not access assignments page: {assignments.status_code}")
        
        # Test schedule page
        print("\n📅 Testing schedule page...")
        schedule = session.get(f"{base_url}/student/schedule/")
        
        if schedule.status_code == 200:
            content = schedule.text
            print("✅ Schedule page accessible")
            
            if "Mathematics" in content and "Algebra II" in content:
                print("❌ Schedule still shows hardcoded Mathematics content")
            elif "English Literature" in content:
                print("✅ Schedule shows dynamic English Literature content")
            elif "No schedule data available" in content:
                print("⚠️ Schedule shows no data message")
            else:
                print("⚠️ Schedule content unclear")
        else:
            print(f"❌ Could not access schedule page: {schedule.status_code}")
        
        print("\n✅ TESTING COMPLETED")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    # Wait a moment for server to start
    time.sleep(2)
    test_student_portal()
