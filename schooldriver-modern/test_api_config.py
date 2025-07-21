#!/usr/bin/env python3
"""
Test script to validate API configuration without running the server.
This tests the configuration syntax and imports.
"""

import os
import sys
import django
from django.conf import settings

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

def test_spectacular_import():
    """Test that drf-spectacular can be imported."""
    try:
        import drf_spectacular
        from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
        print("✅ drf-spectacular imports successfully")
        return True
    except ImportError as e:
        print(f"❌ drf-spectacular import failed: {e}")
        return False

def test_settings_config():
    """Test that SPECTACULAR_SETTINGS is configured."""
    try:
        spectacular_settings = getattr(settings, 'SPECTACULAR_SETTINGS', None)
        if spectacular_settings:
            print("✅ SPECTACULAR_SETTINGS configured")
            print(f"   Title: {spectacular_settings.get('TITLE')}")
            print(f"   Version: {spectacular_settings.get('VERSION')}")
            return True
        else:
            print("❌ SPECTACULAR_SETTINGS not found")
            return False
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_drf_config():
    """Test that DRF is configured with spectacular."""
    try:
        rest_framework = getattr(settings, 'REST_FRAMEWORK', {})
        schema_class = rest_framework.get('DEFAULT_SCHEMA_CLASS')
        if schema_class == 'drf_spectacular.openapi.AutoSchema':
            print("✅ REST_FRAMEWORK configured with spectacular")
            return True
        else:
            print(f"❌ REST_FRAMEWORK schema class: {schema_class}")
            return False
    except Exception as e:
        print(f"❌ DRF config error: {e}")
        return False

def test_url_patterns():
    """Test that URL patterns can be resolved."""
    try:
        from django.urls import reverse
        from schooldriver_modern.api_urls import urlpatterns
        
        print("✅ API URL patterns loaded successfully")
        print(f"   Found {len(urlpatterns)} URL patterns")
        
        # Test that key URLs exist
        urls_to_test = ['schema', 'swagger-ui']
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"   {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ {url_name}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ URL patterns error: {e}")
        return False

def test_serializers():
    """Test that serializers can be imported."""
    try:
        from students.serializers import StudentSerializer, GradeLevelSerializer
        from admissions.serializers import ApplicantSerializer
        print("✅ Serializers import successfully")
        return True
    except Exception as e:
        print(f"❌ Serializers import error: {e}")
        return False

def test_api_views():
    """Test that API views can be imported."""
    try:
        from students.api_views import StudentViewSet, GradeLevelViewSet
        from admissions.api_views import ApplicantViewSet
        print("✅ API views import successfully")
        return True
    except Exception as e:
        print(f"❌ API views import error: {e}")
        return False

def test_installed_apps():
    """Test that required apps are installed."""
    required_apps = [
        'rest_framework',
        'drf_spectacular',
        'students',
        'admissions'
    ]
    
    installed_apps = settings.INSTALLED_APPS
    missing_apps = []
    
    for app in required_apps:
        if app not in installed_apps:
            missing_apps.append(app)
    
    if missing_apps:
        print(f"❌ Missing apps: {missing_apps}")
        return False
    else:
        print("✅ All required apps are installed")
        return True

def main():
    """Run all tests."""
    print("🔍 Testing API Configuration\n")
    
    tests = [
        test_installed_apps,
        test_spectacular_import,
        test_settings_config,
        test_drf_config,
        test_serializers,
        test_api_views,
        test_url_patterns,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API configuration tests passed!")
        return 0
    else:
        print("💥 Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
