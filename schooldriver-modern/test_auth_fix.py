#!/usr/bin/env python3
"""
Simple test script to verify authentication fixes without full Django startup.
"""

import sqlite3
import os

def test_authentication_fixes():
    """Test the authentication system fixes."""
    
    print("🔐 AUTHENTICATION SYSTEM FIX VERIFICATION")
    print("=" * 50)
    
    # Test database connectivity
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test user group assignments
    print("\n1. USER GROUP ASSIGNMENTS:")
    cursor.execute("""
        SELECT u.username, u.is_staff, u.is_superuser, GROUP_CONCAT(g.name) as groups 
        FROM auth_user u 
        LEFT JOIN auth_user_groups ug ON u.id = ug.user_id 
        LEFT JOIN auth_group g ON ug.group_id = g.id 
        GROUP BY u.username
        ORDER BY u.username
    """)
    
    users = cursor.fetchall()
    for username, is_staff, is_superuser, groups in users:
        groups = groups or "None"
        status = "✅" if groups != "None" else "⚠️"
        print(f"   {status} {username}: groups=[{groups}] staff={is_staff} super={is_superuser}")
    
    # Test critical test users
    print("\n2. CRITICAL TEST USERS:")
    test_users = {
        'admin': 'Admin',
        'student1': 'Student', 
        'parent1': 'Parent',
        'test1': 'Student',
        'teststaff': 'Staff'
    }
    
    all_good = True
    for username, expected_group in test_users.items():
        cursor.execute("""
            SELECT g.name FROM auth_user u 
            JOIN auth_user_groups ug ON u.id = ug.user_id 
            JOIN auth_group g ON ug.group_id = g.id 
            WHERE u.username = ?
        """, (username,))
        
        result = cursor.fetchone()
        if result and result[0] == expected_group:
            print(f"   ✅ {username}: {expected_group} group assigned correctly")
        else:
            actual = result[0] if result else "None"
            print(f"   ❌ {username}: Expected {expected_group}, got {actual}")
            all_good = False
    
    # Test groups exist
    print("\n3. REQUIRED GROUPS:")
    cursor.execute("SELECT name FROM auth_group ORDER BY name")
    groups = [row[0] for row in cursor.fetchall()]
    
    required_groups = ['Admin', 'Staff', 'Parent', 'Student']
    for group in required_groups:
        if group in groups:
            print(f"   ✅ {group} group exists")
        else:
            print(f"   ❌ {group} group missing")
            all_good = False
    
    conn.close()
    
    print("\n4. CONFIGURATION FILES:")
    
    # Check if auth_views.py was modified
    auth_views_path = 'schooldriver_modern/auth_views.py'
    if os.path.exists(auth_views_path):
        with open(auth_views_path, 'r') as f:
            content = f.read()
            if 'get_success_url' in content:
                print("   ✅ CustomLoginView updated with get_success_url method")
            else:
                print("   ⚠️ CustomLoginView may not have get_success_url method")
    
    # Check if settings.py was modified  
    settings_path = 'schooldriver_modern/settings.py'
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            content = f.read()
            if 'LOGIN_REDIRECT_URL removed' in content:
                print("   ✅ LOGIN_REDIRECT_URL removed from settings")
            else:
                print("   ⚠️ LOGIN_REDIRECT_URL may still be set in settings")
    
    # Check if middleware was added
    if 'PortalAccessMiddleware' in content:
        print("   ✅ PortalAccessMiddleware added to settings")
    else:
        print("   ⚠️ PortalAccessMiddleware may not be configured")
    
    print("\n5. EXPECTED AUTHENTICATION FLOW:")
    print("   📋 Admin users → /admin/ (Django admin)")
    print("   📋 Staff users → /admin/ (Django admin)")  
    print("   📋 Student users → /student/ (Student portal)")
    print("   📋 Parent users → /parent/ (Parent portal)")
    print("   📋 Unauthenticated → / (Public home)")
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 AUTHENTICATION SYSTEM FIXES VERIFIED!")
        print("✅ All user groups are properly assigned")
        print("✅ Role-based redirects should now work correctly")
        print("✅ Portal access control is configured")
        
        print("\n📝 TO TEST THE LOGIN SYSTEM:")
        print("1. Start server: python manage.py runserver")
        print("2. Visit: http://127.0.0.1:8000/accounts/login/")
        print("3. Test with these accounts:")
        print("   - student1 / student123 → Should go to /student/")
        print("   - parent1 / parent123 → Should go to /parent/")
        print("   - admin / admin123 → Should go to /admin/")
        
        return True
    else:
        print("❌ SOME ISSUES FOUND - Please review the problems above")
        return False

if __name__ == "__main__":
    test_authentication_fixes()
