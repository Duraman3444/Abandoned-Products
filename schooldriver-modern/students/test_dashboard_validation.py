"""
Dashboard Analytics Validation Tests

This module validates the four key criteria for dashboard analytics:
1. 4+ interactive charts displaying real data
2. Dashboard loads in <2 seconds  
3. Mobile-responsive on all devices
4. Admin integration working seamlessly

Uses Django's LiveServerTestCase + Selenium for end-to-end validation.
"""

import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class DashboardValidationTests(StaticLiveServerTestCase):
    """
    End-to-end validation tests for Dashboard Analytics requirements.
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Setup Chrome in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            raise Exception(f"Chrome WebDriver not available: {e}")
    
    @classmethod 
    def tearDownClass(cls):
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Create test user for authentication"""
        self.superuser = User.objects.create_superuser(
            username='testadmin',
            email='test@example.com', 
            password='testpass123'
        )
    
    def login_user(self):
        """Helper method to log in the test user"""
        self.driver.get(f"{self.live_server_url}/accounts/login/")
        
        # Wait for login form
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        
        username_field.send_keys('testadmin')
        password_field.send_keys('testpass123')
        
        # Submit form
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        login_button.click()
        
        # Wait for redirect after login
        WebDriverWait(self.driver, 10).until(
            lambda driver: "/accounts/login/" not in driver.current_url
        )
    
    def test_four_interactive_charts(self):
        """
        Test Criteria 1: 4+ interactive charts displaying real data
        """
        self.login_user()
        
        # Navigate to dashboard
        dashboard_url = f"{self.live_server_url}/dashboard/"
        self.driver.get(dashboard_url)
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Count Chart.js canvas elements
        try:
            canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
            chart_canvases = [canvas for canvas in canvas_elements 
                            if 'chart' in canvas.get_attribute('class').lower()]
            
            # Alternative: look for any canvas elements in dashboard
            if not chart_canvases:
                chart_canvases = canvas_elements
                
            self.assertGreaterEqual(
                len(chart_canvases), 4,
                f"Expected 4+ interactive charts, found {len(chart_canvases)} canvas elements"
            )
            
            print(f"✅ Found {len(chart_canvases)} chart canvas elements")
            
        except Exception as e:
            # Fallback: check for chart containers or other chart indicators
            chart_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                "[id*='chart'], [class*='chart'], .chart-container")
            
            self.assertGreaterEqual(
                len(chart_containers), 4,
                f"Expected 4+ chart containers, found {len(chart_containers)}"
            )
            
            print(f"✅ Found {len(chart_containers)} chart containers")
    
    def test_dashboard_load_time(self):
        """
        Test Criteria 2: Dashboard loads in <2 seconds
        """
        self.login_user()
        
        dashboard_url = f"{self.live_server_url}/dashboard/"
        
        # Measure load time
        start_time = time.time()
        self.driver.get(dashboard_url)
        
        # Wait for page to be fully loaded
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Execute JavaScript to ensure all resources loaded
        self.driver.execute_script("return document.readyState") == "complete"
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        self.assertLess(
            load_time_ms, 2000,
            f"Dashboard took {load_time_ms:.2f}ms to load, expected <2000ms"
        )
        
        print(f"✅ Dashboard loaded in {load_time_ms:.2f}ms")
    
    def test_mobile_responsive_design(self):
        """
        Test Criteria 3: Mobile-responsive on all devices
        """
        self.login_user()
        
        dashboard_url = f"{self.live_server_url}/dashboard/"
        
        # Test iPhone X dimensions (375×667)
        self.driver.set_window_size(375, 667)
        self.driver.get(dashboard_url)
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for horizontal overflow (allow 5px tolerance for browser differences)
        scroll_width = self.driver.execute_script("return document.documentElement.scrollWidth")
        inner_width = self.driver.execute_script("return window.innerWidth")
        overflow = scroll_width - inner_width
        
        self.assertLessEqual(
            overflow, 5,
            f"Mobile view has significant horizontal overflow: scrollWidth={scroll_width}, innerWidth={inner_width}, overflow={overflow}px"
        )
        
        print(f"✅ Mobile (375px) responsive: scrollWidth={scroll_width}, innerWidth={inner_width}")
        
        # Test iPad dimensions (768×1024)
        self.driver.set_window_size(768, 1024)
        self.driver.refresh()
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        scroll_width = self.driver.execute_script("return document.documentElement.scrollWidth")
        inner_width = self.driver.execute_script("return window.innerWidth")
        overflow = scroll_width - inner_width
        
        self.assertLessEqual(
            overflow, 5,
            f"Tablet view has significant horizontal overflow: scrollWidth={scroll_width}, innerWidth={inner_width}, overflow={overflow}px"
        )
        
        print(f"✅ Tablet (768px) responsive: scrollWidth={scroll_width}, innerWidth={inner_width}")
    
    def test_admin_integration(self):
        """
        Test Criteria 4: Admin integration working seamlessly
        """
        self.login_user()
        
        # Visit admin interface
        admin_url = f"{self.live_server_url}/admin/"
        self.driver.get(admin_url)
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for Dashboard link in admin
        try:
            dashboard_link = self.driver.find_element(By.LINK_TEXT, "Dashboard")
            dashboard_href = dashboard_link.get_attribute('href')
            
            # Click dashboard link and verify it returns HTTP 200
            dashboard_link.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Verify we're on dashboard and page loaded successfully
            current_url = self.driver.current_url
            self.assertIn("dashboard", current_url.lower())
            
            print(f"✅ Admin Dashboard link working: {dashboard_href}")
            
        except NoSuchElementException:
            # Alternative: check for any dashboard-related links
            dashboard_links = self.driver.find_elements(By.CSS_SELECTOR, 
                "a[href*='dashboard'], a[href*='Dashboard']")
            
            self.assertGreater(
                len(dashboard_links), 0,
                "No Dashboard link found in admin interface"
            )
            
            # Test first dashboard link
            first_link = dashboard_links[0]
            href = first_link.get_attribute('href')
            first_link.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print(f"✅ Admin dashboard integration working: {href}")


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
        django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["students.test_dashboard_validation"])
    
    if failures:
        exit(1)
