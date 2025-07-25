#!/usr/bin/env python3
"""
Test mobile features implementation for SchoolDriver Parent Portal
"""
import os
import sys
import django
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

class MobileFeaturesTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        
    def test_pwa_manifest(self):
        """Test PWA manifest accessibility and content"""
        try:
            response = requests.get(f"{self.base_url}/static/manifest.json")
            if response.status_code == 200:
                manifest = response.json()
                
                # Check required PWA fields
                required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
                for field in required_fields:
                    if field not in manifest:
                        self.results.append(f"❌ PWA Manifest missing required field: {field}")
                        return False
                
                # Check icons
                if len(manifest.get('icons', [])) < 3:
                    self.results.append(f"❌ PWA Manifest needs more icon sizes")
                    return False
                
                self.results.append("✅ PWA Manifest is valid and accessible")
                return True
            else:
                self.results.append(f"❌ PWA Manifest not accessible: {response.status_code}")
                return False
        except Exception as e:
            self.results.append(f"❌ PWA Manifest test failed: {e}")
            return False
    
    def test_service_worker(self):
        """Test service worker accessibility"""
        try:
            response = requests.get(f"{self.base_url}/static/js/sw.js")
            if response.status_code == 200:
                sw_content = response.text
                
                # Check for key service worker features
                required_features = [
                    'install', 'activate', 'fetch', 'push', 'notificationclick'
                ]
                
                for feature in required_features:
                    if feature not in sw_content:
                        self.results.append(f"❌ Service Worker missing event listener: {feature}")
                        return False
                
                self.results.append("✅ Service Worker is accessible and has required features")
                return True
            else:
                self.results.append(f"❌ Service Worker not accessible: {response.status_code}")
                return False
        except Exception as e:
            self.results.append(f"❌ Service Worker test failed: {e}")
            return False
    
    def test_pwa_javascript(self):
        """Test PWA JavaScript functionality"""
        try:
            response = requests.get(f"{self.base_url}/static/js/pwa.js")
            if response.status_code == 200:
                pwa_content = response.text
                
                # Check for key PWA features
                required_features = [
                    'PWAManager', 'serviceWorker', 'beforeinstallprompt', 
                    'GradeWidget', 'requestNotificationPermission'
                ]
                
                for feature in required_features:
                    if feature not in pwa_content:
                        self.results.append(f"❌ PWA JS missing feature: {feature}")
                        return False
                
                self.results.append("✅ PWA JavaScript has all required features")
                return True
            else:
                self.results.append(f"❌ PWA JavaScript not accessible: {response.status_code}")
                return False
        except Exception as e:
            self.results.append(f"❌ PWA JavaScript test failed: {e}")
            return False
    
    def test_app_icons(self):
        """Test that app icons exist"""
        icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
        missing_icons = []
        
        for size in icon_sizes:
            response = requests.get(f"{self.base_url}/static/img/icon-{size}x{size}.png")
            if response.status_code != 200:
                missing_icons.append(f"{size}x{size}")
        
        if missing_icons:
            self.results.append(f"❌ Missing app icons: {', '.join(missing_icons)}")
            return False
        else:
            self.results.append("✅ All app icons are accessible")
            return True
    
    def test_mobile_responsiveness(self):
        """Test mobile responsiveness with Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Test mobile viewport
            driver.set_window_size(375, 667)  # iPhone SE size
            driver.get(f"{self.base_url}/parent/")
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if page is responsive
            body = driver.find_element(By.TAG_NAME, "body")
            if body.size['width'] <= 375:
                self.results.append("✅ Page is mobile responsive")
                mobile_responsive = True
            else:
                self.results.append("❌ Page is not properly responsive on mobile")
                mobile_responsive = False
            
            driver.quit()
            return mobile_responsive
            
        except Exception as e:
            self.results.append(f"❌ Mobile responsiveness test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints for mobile features"""
        try:
            # Test quick grades API (this would normally require authentication)
            response = requests.get(f"{self.base_url}/parent/api/quick-grades/")
            
            # Since we're not authenticated, we should get a redirect or 403
            if response.status_code in [302, 403, 401]:
                self.results.append("✅ Quick grades API endpoint exists and requires authentication")
                return True
            else:
                self.results.append(f"❌ Quick grades API unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            self.results.append(f"❌ API endpoints test failed: {e}")
            return False
    
    def test_document_upload_urls(self):
        """Test document upload URL accessibility"""
        try:
            # Test document upload URL (should redirect to login)
            response = requests.get(f"{self.base_url}/parent/upload-document/")
            
            if response.status_code in [302, 403, 401]:
                self.results.append("✅ Document upload URL exists and requires authentication")
                document_upload = True
            else:
                self.results.append(f"❌ Document upload URL unexpected response: {response.status_code}")
                document_upload = False
            
            # Test document list URL
            response = requests.get(f"{self.base_url}/parent/documents/")
            
            if response.status_code in [302, 403, 401]:
                self.results.append("✅ Document list URL exists and requires authentication")
                document_list = True
            else:
                self.results.append(f"❌ Document list URL unexpected response: {response.status_code}")
                document_list = False
            
            return document_upload and document_list
            
        except Exception as e:
            self.results.append(f"❌ Document upload URLs test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all mobile feature tests"""
        print("🧪 Testing Mobile Features Implementation...")
        print("=" * 50)
        
        tests = [
            ("PWA Manifest", self.test_pwa_manifest),
            ("Service Worker", self.test_service_worker),
            ("PWA JavaScript", self.test_pwa_javascript),
            ("App Icons", self.test_app_icons),
            ("API Endpoints", self.test_api_endpoints),
            ("Document Upload URLs", self.test_document_upload_urls),
            # ("Mobile Responsiveness", self.test_mobile_responsiveness),  # Requires Chrome driver
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\nTesting {test_name}...")
            if test_func():
                passed += 1
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS:")
        for result in self.results:
            print(result)
        
        print(f"\n📈 SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All mobile features tests PASSED!")
            return True
        else:
            print("⚠️  Some tests failed. Check implementation.")
            return False

def main():
    """Run mobile features tests"""
    tester = MobileFeaturesTester()
    return tester.run_all_tests()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
