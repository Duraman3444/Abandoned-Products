#!/usr/bin/env python3
"""
Test the expanded profile editing functionality.
"""
import os
import sys
import django

# Setup Django
sys.path.append('./schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from schooldriver_modern.models import UserProfile

def test_profile_fields():
    """Test that profile fields can be set and retrieved."""
    print("🧪 Testing expanded profile functionality...")
    
    # Get the test user
    try:
        user = User.objects.get(username='test')
        profile = user.profile
        
        # Test setting new fields
        profile.date_of_birth = '2008-10-08'
        profile.phone_number = '(555) 123-4567'
        profile.address = '123 Maple Street, Springfield, IL 62701'
        profile.emergency_contact_1_name = 'Mary Anderson'
        profile.emergency_contact_1_relationship = 'grandparent'
        profile.emergency_contact_1_phone = '(555) 987-6543'
        profile.emergency_contact_2_name = 'David Johnson'
        profile.emergency_contact_2_relationship = 'other'
        profile.emergency_contact_2_phone = '(555) 987-6544'
        profile.emergency_address = '123 Maple Street, Springfield, IL 62701'
        profile.email_notifications = True
        profile.sms_notifications = False
        profile.parent_portal_access = True
        
        profile.save()
        
        # Verify fields were saved
        updated_profile = UserProfile.objects.get(user=user)
        
        print("✅ Profile fields updated successfully:")
        print(f"   Date of Birth: {updated_profile.date_of_birth}")
        print(f"   Phone: {updated_profile.phone_number}")
        print(f"   Address: {updated_profile.address}")
        print(f"   Primary Contact: {updated_profile.emergency_contact_1_name} ({updated_profile.emergency_contact_1_relationship})")
        print(f"   Secondary Contact: {updated_profile.emergency_contact_2_name} ({updated_profile.emergency_contact_2_relationship})")
        print(f"   Email Notifications: {updated_profile.email_notifications}")
        print(f"   SMS Notifications: {updated_profile.sms_notifications}")
        print(f"   Parent Portal Access: {updated_profile.parent_portal_access}")
        
        print("\n🎉 All profile fields are working correctly!")
        return True
        
    except User.DoesNotExist:
        print("❌ Test user not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_profile_fields()
    sys.exit(0 if success else 1)
