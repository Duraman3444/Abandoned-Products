#!/usr/bin/env python3

import os
import sys
import django
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Set up Django environment
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

def test_emergency_contact_functionality():
    """Test emergency contact links and functionality in detail"""
    
    print("🧪 Testing Emergency Contact Functionality")
    print("=" * 50)
    
    # Test Django URLs first
    client = Client()
    
    # Login using Django test client
    try:
        user = User.objects.get(username='parent1')
        client.force_login(user)
        print("✅ Logged in as parent1 via Django client")
    except User.DoesNotExist:
        print("❌ parent1 user does not exist")
        return False
    
    # Test emergency contacts main page
    try:
        response = client.get('/parent/emergency-contacts/')
        print(f"Emergency contacts page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Emergency contacts page accessible via Django client")
            # Check if response contains expected content
            content = response.content.decode()
            if "Add Contact" in content:
                print("✅ 'Add Contact' button found in response")
            else:
                print("❌ 'Add Contact' button NOT found in response")
        else:
            print(f"❌ Emergency contacts page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing emergency contacts: {e}")
    
    # Test add emergency contact page
    try:
        response = client.get('/parent/emergency-contacts/add/')
        print(f"Add emergency contact page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Add emergency contact page accessible")
        else:
            print(f"❌ Add emergency contact page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing add emergency contact: {e}")
    
    # Test add pickup person page
    try:
        response = client.get('/parent/pickup-persons/add/')
        print(f"Add pickup person page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Add pickup person page accessible")
        else:
            print(f"❌ Add pickup person page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing add pickup person: {e}")
    
    # Test medical information page
    try:
        response = client.get('/parent/medical-information/')
        print(f"Medical information page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Medical information page accessible")
        else:
            print(f"❌ Medical information page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing medical information: {e}")
    
    # Test student profile page
    try:
        response = client.get('/parent/child/')
        print(f"Student profile page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Student profile page accessible")
        else:
            print(f"❌ Student profile page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing student profile: {e}")
        
    return True

if __name__ == "__main__":
    test_emergency_contact_functionality()
