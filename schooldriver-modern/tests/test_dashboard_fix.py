"""
Tests for dashboard chart rendering fixes.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings
# Selenium imports commented out - can be enabled if selenium is installed
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
import json
import time


class DashboardFixTests(TestCase):
    """Test dashboard chart rendering and metrics after dark theme fixes."""
    
    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass'
        )
        self.client = Client()
        self.client.login(username='testadmin', password='testpass')
    
    def test_dashboard_page_loads(self):
        """Test that dashboard page loads successfully."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
        self.assertContains(response, 'chart-container')
    
    def test_dashboard_context_data(self):
        """Test that dashboard context contains required data."""
        response = self.client.get(reverse('dashboard'))
        self.assertIn('dashboard_data', response.context)
        self.assertIn('dashboard_data_json', response.context)
        
        dashboard_data = response.context['dashboard_data']
        
        # Verify all required data sections
        self.assertIn('pipeline', dashboard_data)
        self.assertIn('documents', dashboard_data)
        self.assertIn('status', dashboard_data)
        self.assertIn('trends', dashboard_data)
        self.assertIn('summary', dashboard_data)
    
    def test_metrics_present(self):
        """Test that metric cards display expected demo stats."""
        response = self.client.get(reverse('dashboard'))
        dashboard_data = response.context['dashboard_data']
        summary = dashboard_data['summary']
        
        # Test expected demo stats: 1240 total applications, 418 acceptances, etc.
        expected_applications = sum(dashboard_data['trends']['applications'])
        expected_acceptances = sum(dashboard_data['trends']['acceptances'])
        expected_rate = round(expected_acceptances / expected_applications * 100, 1)
        expected_pending = dashboard_data['status']['values'][0] + dashboard_data['status']['values'][1]
        
        self.assertEqual(summary['total_applications'], expected_applications)
        self.assertEqual(summary['total_acceptances'], expected_acceptances)
        self.assertEqual(summary['acceptance_rate'], expected_rate)
        self.assertEqual(summary['pending_applications'], expected_pending)
        
        # Check that these appear in the rendered template
        self.assertContains(response, str(summary['total_applications']))
        self.assertContains(response, str(summary['total_acceptances']))
        self.assertContains(response, f"{summary['acceptance_rate']}%")
        self.assertContains(response, str(summary['pending_applications']))
    
    def test_chart_canvas_elements_present(self):
        """Test that all four chart canvas elements are present."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for all four chart canvas elements
        self.assertContains(response, 'id="pipelineChart"')
        self.assertContains(response, 'id="documentsChart"')
        self.assertContains(response, 'id="statusChart"')
        self.assertContains(response, 'id="trendsChart"')
    
    def test_chart_javascript_present(self):
        """Test that Chart.js and initialization scripts are present."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for Chart.js library
        self.assertContains(response, 'chart.min.js')
        
        # Check for chart initialization functions
        self.assertContains(response, 'initializeCharts()')
        self.assertContains(response, 'setupChartDefaults()')
        self.assertContains(response, 'Chart.defaults.color')
        
        # Check for dashboard data being passed to JavaScript
        self.assertContains(response, 'dashboardData =')
    
    def test_dark_theme_css_applied(self):
        """Test that dark theme CSS is properly applied."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for dark theme CSS
        self.assertContains(response, 'dashboard.css')
        self.assertContains(response, 'dashboard-dark')
        
        # Check for dark theme elements in the template
        self.assertContains(response, 'dashboard-container')
        self.assertContains(response, 'chart-card')


# Selenium tests commented out - can be enabled if selenium is installed
# class DashboardSeleniumTests(TestCase):
#     """Selenium tests for chart rendering functionality."""
#     
#     @classmethod
#     def setUpClass(cls):
#         """Set up Selenium WebDriver."""
#         super().setUpClass()
#         
#         # Set up Chrome options for headless testing
#         chrome_options = Options()
#         chrome_options.add_argument('--headless')
#         chrome_options.add_argument('--no-sandbox')
#         chrome_options.add_argument('--disable-dev-shm-usage')
#         chrome_options.add_argument('--disable-gpu')
#         
#         try:
#             cls.driver = webdriver.Chrome(options=chrome_options)
#             cls.driver.implicitly_wait(10)
#         except Exception as e:
#             # Skip selenium tests if Chrome driver not available
#             cls.driver = None
#             print(f"Selenium tests skipped: {e}")
#     
#     @classmethod
#     def tearDownClass(cls):
#         """Clean up WebDriver."""
#         if cls.driver:
#             cls.driver.quit()
#         super().tearDownClass()
#     
#     def setUp(self):
#         """Set up test user."""
#         if not self.driver:
#             self.skipTest("Chrome WebDriver not available")
#             
#         self.user = User.objects.create_superuser(
#             username='testadmin',
#             email='admin@test.com',
#             password='testpass'
#         )
#     
#     def test_charts_render(self):
#         """Test that canvas elements become non-empty within 1 second using Selenium."""
#         if not self.driver:
#             self.skipTest("Chrome WebDriver not available")
#         
#         # Login first
#         self.driver.get(f'{self.live_server_url}/admin/login/')
#         username_input = self.driver.find_element(By.NAME, 'username')
#         password_input = self.driver.find_element(By.NAME, 'password')
#         username_input.send_keys('testadmin')
#         password_input.send_keys('testpass')
#         self.driver.find_element(By.XPATH, '//input[@type="submit"]').click()
#         
#         # Navigate to dashboard
#         self.driver.get(f'{self.live_server_url}/dashboard/')
#         
#         # Wait for page to load
#         WebDriverWait(self.driver, 10).until(
#             EC.presence_of_element_located((By.CLASS_NAME, 'dashboard-container'))
#         )
#         
#         # Wait for Chart.js to load and charts to initialize
#         time.sleep(2)
#         
#         # Check that all four canvas elements exist and have content
#         canvas_ids = ['pipelineChart', 'documentsChart', 'statusChart', 'trendsChart']
#         
#         for canvas_id in canvas_ids:
#             canvas = self.driver.find_element(By.ID, canvas_id)
#             
#             # Check that canvas is visible
#             self.assertTrue(canvas.is_displayed(), f"{canvas_id} canvas should be visible")
#             
#             # Check that canvas has dimensions (indicating it's rendered)
#             width = canvas.get_attribute('width')
#             height = canvas.get_attribute('height')
#             
#             self.assertIsNotNone(width, f"{canvas_id} should have width attribute")
#             self.assertIsNotNone(height, f"{canvas_id} should have height attribute")
#             self.assertNotEqual(width, '0', f"{canvas_id} width should not be 0")
#             self.assertNotEqual(height, '0', f"{canvas_id} height should not be 0")
#         
#         # Check for Chart.js generated content
#         charts_rendered = self.driver.execute_script("""
#             return Object.keys(Chart.instances).length > 0;
#         """)
#         
#         self.assertTrue(charts_rendered, "Chart.js should have created chart instances")
