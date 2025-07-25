#!/usr/bin/env python3
"""Fix parent data and check parent portal styling."""

import os
import sys
import django

# Add the Django app directory to the Python path
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User

def fix_parent_name():
    """Fix the parent1 user name to be consistent."""
    
    print("🔧 FIXING PARENT DATA")
    print("=" * 30)
    
    # Find parent1 user
    parent_user = User.objects.filter(username='parent1').first()
    if not parent_user:
        print("❌ Parent1 user not found!")
        return
    
    print(f"📋 Current parent name: {parent_user.first_name} {parent_user.last_name}")
    
    # Update the name to be consistent with Emma Smith
    parent_user.first_name = "Michael"
    parent_user.last_name = "Smith"  # Changed from Adams to Smith
    parent_user.email = "michael.smith@parent.com"
    parent_user.save()
    
    print(f"✅ Updated parent name to: {parent_user.first_name} {parent_user.last_name}")
    print(f"✅ Updated email to: {parent_user.email}")
    
    # Also check if there are any parent profile records that need updating
    try:
        from parent_portal.models import ParentProfile
        profile = ParentProfile.objects.filter(user=parent_user).first()
        if profile:
            profile.full_name = f"{parent_user.first_name} {parent_user.last_name}"
            profile.save()
            print("✅ Updated parent profile")
    except:
        print("ℹ️ No parent profile model found")

if __name__ == '__main__':
    fix_parent_name()
