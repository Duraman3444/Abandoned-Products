#!/usr/bin/env python3
"""
Test the new student portal edit profile page functionality.
"""
import os
import sys
import django

# Setup Django
sys.path.append('./schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_edit_profile_page():
    """Test that the edit profile page is accessible and functional."""
    print("🧪 Testing student portal edit profile page...")
    
    client = Client()
    
    try:
        # Get the test user
        user = User.objects.get(username='test')
        
        # Login
        login_success = client.login(username='test', password='test')
        if not login_success:
            print("❌ Login failed")
            return False
        
        print("✅ Login successful")
        
        # Test GET request to edit profile page
        edit_url = reverse('student_portal:profile_edit')
        response = client.get(edit_url)
        
        print(f"📝 Edit profile page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Edit profile page accessible")
            
            # Check if key fields are in the form
            content = response.content.decode()
            required_fields = [
                'name="first_name"',
                'name="last_name"',
                'name="email"',
                'name="date_of_birth"',
                'name="phone_number"',
                'name="address"',
                'name="emergency_contact_1_name"',
                'name="emergency_contact_1_relationship"',
                'name="emergency_contact_1_phone"',
                'name="emergency_contact_2_name"',
                'name="emergency_contact_2_relationship"',
                'name="emergency_contact_2_phone"',
                'name="emergency_address"',
                'name="email_notifications"',
                'name="sms_notifications"',
                'name="parent_portal_access"'
            ]
            
            fields_found = 0
            for field in required_fields:
                if field in content:
                    fields_found += 1
                    print(f"✅ Found field: {field}")
                else:
                    print(f"❌ Missing field: {field}")
            
            print(f"\n📊 Summary: {fields_found}/{len(required_fields)} fields found")
            
            if fields_found == len(required_fields):
                print("🎉 All required fields are present in the edit form!")
                return True
            else:
                print("💥 Some required fields are missing!")
                return False
                
        else:
            print(f"❌ Edit profile page not accessible (status: {response.status_code})")
            return False
            
    except User.DoesNotExist:
        print("❌ Test user not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_edit_profile_page()
    if success:
        print("\n🎉 Student portal edit profile page is working correctly!")
        print("   URL: /student/profile/edit/")
        print("   All emergency contact fields included")
        print("   Full page form (not popup)")
    else:
        print("\n💥 Student portal edit profile page has issues!")
    
    sys.exit(0 if success else 1)
