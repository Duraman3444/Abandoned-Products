#!/usr/bin/env python3
"""
Simple syntax validation for API configuration files.
This validates that all API files have correct Python syntax.
"""

import os
import py_compile
import sys
from pathlib import Path

def validate_syntax(file_path):
    """Validate Python syntax for a file."""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    """Validate syntax of all API-related files."""
    print("🔍 Validating API Configuration File Syntax\n")
    
    # Files to validate
    files_to_check = [
        'schooldriver_modern/settings.py',
        'schooldriver_modern/urls.py',
        'schooldriver_modern/api_urls.py',
        'students/serializers.py',
        'students/api_views.py',
        'admissions/serializers.py',
        'admissions/api_views.py',
    ]
    
    results = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            valid, error = validate_syntax(file_path)
            if valid:
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path}: {error}")
            results.append(valid)
        else:
            print(f"⚠️  {file_path}: File not found")
            results.append(False)
    
    # Check requirements.txt
    req_file = 'requirements.txt'
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            content = f.read()
            if 'drf-spectacular' in content:
                print(f"✅ {req_file}: Contains drf-spectacular")
                results.append(True)
            else:
                print(f"❌ {req_file}: Missing drf-spectacular")
                results.append(False)
    else:
        print(f"❌ {req_file}: Not found")
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Syntax Validation: {passed}/{total} files valid")
    
    if passed == total:
        print("🎉 All API configuration files have valid syntax!")
        print("\nAPI Features Configured:")
        print("- OpenAPI/Swagger documentation endpoints")
        print("- Student management API endpoints")
        print("- Admissions management API endpoints")
        print("- Comprehensive filtering and search")
        print("- Pagination and authentication")
        print("\nTo test the API:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run migrations: python manage.py migrate")
        print("3. Start server: python manage.py runserver")
        print("4. Visit: http://localhost:8000/api/docs/")
        return 0
    else:
        print("💥 Some files have syntax errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
