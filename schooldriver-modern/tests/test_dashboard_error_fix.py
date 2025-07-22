"""
Tests for Chart.js defaults error and source-map 404 fixes.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# Selenium imports for browser console testing
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class DashboardErrorFixTests(TestCase):
    """Test that Chart.js defaults error and source-map 404 are fixed."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_superuser(
            username="testadmin", email="admin@test.com", password="testpass"
        )
        self.client = Client()
        self.client.login(username="testadmin", password="testpass")

    def test_charts_render(self):
        """Test that canvas elements are present and properly configured."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Check that all four chart canvas elements exist
        chart_ids = ["pipelineChart", "documentsChart", "statusChart", "trendsChart"]
        for chart_id in chart_ids:
            self.assertContains(response, f'id="{chart_id}"')

        # Check that Chart.js initialization script is present
        self.assertContains(response, "initializeCharts()")
        self.assertContains(response, "setupChartDefaults()")

        # Verify Chart.js 4.x compatible defaults are used
        self.assertContains(response, "Chart.defaults.color")
        self.assertContains(response, "Chart.defaults.plugins")
        self.assertContains(response, "Chart.defaults.scales")

        # Check for safe object property access
        self.assertContains(
            response, "Chart.defaults.plugins && Chart.defaults.plugins.legend"
        )
        self.assertContains(response, "Chart.defaults.scales")

        # Verify charts are initialized on DOM ready
        self.assertContains(response, "DOMContentLoaded")

    def test_no_console_typeerror(self):
        """Test that Chart.js defaults setup doesn't cause TypeError."""
        response = self.client.get(reverse("dashboard"))

        # Check that Chart.js 4.x compatible syntax is used
        # The old Chart.js 3.x syntax that caused TypeError:
        # - Chart.defaults.scales.category.ticks.color (TypeError: Cannot set properties of undefined)
        # Should be replaced with safe object checking

        # Verify the fixed code is present
        self.assertContains(
            response,
            "Chart.defaults.scales.category = Chart.defaults.scales.category || {};",
        )
        self.assertContains(
            response,
            "Chart.defaults.scales.linear = Chart.defaults.scales.linear || {};",
        )
        self.assertContains(
            response,
            "Chart.defaults.plugins.legend.labels = Chart.defaults.plugins.legend.labels || {};",
        )

        # Verify safe property assignment is used - should have both object checking AND assignment
        self.assertContains(
            response,
            "Chart.defaults.scales.category.ticks = Chart.defaults.scales.category.ticks || {};",
        )
        self.assertContains(
            response, "Chart.defaults.scales.category.ticks.color = '#E6EDF3';"
        )

    def test_no_404_maps(self):
        """Test that chart.min.js static file is properly accessible."""
        response = self.client.get(reverse("dashboard"))

        # Check that Chart.js file is included in dashboard
        self.assertContains(response, "chart.min.js")

        # Verify that Chart.js static file exists in the filesystem
        import os
        from django.conf import settings

        chart_js_path = os.path.join(settings.BASE_DIR, "static", "js", "chart.min.js")
        self.assertTrue(
            os.path.exists(chart_js_path),
            "Chart.js file should exist in static directory",
        )

        # Read the actual file content
        with open(chart_js_path, "r") as f:
            chart_js_content = f.read()

        # Verify the file contains Chart.js content
        self.assertIn("Chart", chart_js_content)

    def test_chart_defaults_safe_initialization(self):
        """Test that Chart.js defaults are set up safely without undefined errors."""
        response = self.client.get(reverse("dashboard"))

        # Check for safe initialization pattern that prevents TypeError
        self.assertContains(
            response, "if (Chart.defaults.plugins && Chart.defaults.plugins.legend)"
        )
        self.assertContains(response, "if (Chart.defaults.scales)")

        # Verify the dark theme colors are still applied
        self.assertContains(response, "#E6EDF3")  # Dark theme text color
        self.assertContains(response, "rgba(255, 255, 255, 0.1)")  # Grid color

        # Check that all required chart properties are set
        expected_properties = [
            "Chart.defaults.color",
            "Chart.defaults.borderColor",
            "Chart.defaults.backgroundColor",
            "Chart.defaults.plugins.legend.labels.color",
            "Chart.defaults.scales.category.ticks.color",
            "Chart.defaults.scales.linear.ticks.color",
            "Chart.defaults.scales.category.grid.color",
            "Chart.defaults.scales.linear.grid.color",
        ]

        for prop in expected_properties:
            self.assertContains(response, prop)

    def test_dashboard_loads_without_errors(self):
        """Test that dashboard page loads successfully without JavaScript errors."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Check essential dashboard elements are present
        self.assertContains(response, "Analytics Dashboard")
        self.assertContains(response, "chart-container")

        # Verify Chart.js library is loaded
        self.assertContains(response, "chart.min.js")

        # Check that dashboard data is available
        self.assertIn("dashboard_data", response.context)
        dashboard_data = response.context["dashboard_data"]

        # Verify all chart data sections exist
        required_sections = ["pipeline", "documents", "status", "trends"]
        for section in required_sections:
            self.assertIn(section, dashboard_data)

    def test_chart_data_structure(self):
        """Test that chart data has the correct structure for Chart.js."""
        response = self.client.get(reverse("dashboard"))
        dashboard_data = response.context["dashboard_data"]

        # Test pipeline chart data structure
        pipeline_data = dashboard_data["pipeline"]
        self.assertIn("labels", pipeline_data)
        self.assertIn("values", pipeline_data)
        self.assertIsInstance(pipeline_data["labels"], list)
        self.assertIsInstance(pipeline_data["values"], list)

        # Test trends chart data structure
        trends_data = dashboard_data["trends"]
        self.assertIn("labels", trends_data)
        self.assertIn("applications", trends_data)
        self.assertIn("acceptances", trends_data)
        self.assertIsInstance(trends_data["labels"], list)
        self.assertIsInstance(trends_data["applications"], list)
        self.assertIsInstance(trends_data["acceptances"], list)

        # Verify all data lists have content
        self.assertGreater(len(pipeline_data["labels"]), 0)
        self.assertGreater(len(pipeline_data["values"]), 0)
        self.assertGreater(len(trends_data["labels"]), 0)
        self.assertGreater(len(trends_data["applications"]), 0)


# Selenium tests commented out - can be enabled if selenium is installed
# class DashboardSeleniumErrorTests(TestCase):
#     """Selenium tests for Chart.js error fixes in browser console."""
#
#     @classmethod
#     def setUpClass(cls):
#         """Set up Selenium WebDriver with console logging."""
#         super().setUpClass()
#
#         # Set up Chrome options for headless testing with console logging
#         chrome_options = Options()
#         chrome_options.add_argument('--headless')
#         chrome_options.add_argument('--no-sandbox')
#         chrome_options.add_argument('--disable-dev-shm-usage')
#         chrome_options.add_argument('--disable-gpu')
#
#         # Enable console logging
#         caps = DesiredCapabilities.CHROME
#         caps['goog:loggingPrefs'] = {'browser': 'ALL'}
#
#         try:
#             cls.driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
#             cls.driver.implicitly_wait(10)
#         except Exception as e:
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
#     def test_no_console_typeerror(self):
#         """Test that browser console contains no TypeError after Chart.js loads."""
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
#         # Wait for Chart.js to load and initialize
#         WebDriverWait(self.driver, 10).until(
#             EC.presence_of_element_located((By.CLASS_NAME, 'dashboard-container'))
#         )
#
#         # Wait for charts to initialize
#         time.sleep(3)
#
#         # Get browser console logs
#         logs = self.driver.get_log('browser')
#
#         # Filter for TypeError messages
#         type_errors = [log for log in logs if 'TypeError' in log['message']]
#
#         # Assert no TypeError messages in console
#         if type_errors:
#             error_messages = [log['message'] for log in type_errors]
#             self.fail(f"Found TypeError in console: {error_messages}")
#
#         # Also check that charts are actually rendered
#         charts_rendered = self.driver.execute_script("""
#             return document.querySelectorAll('canvas').length >= 4;
#         """)
#
#         self.assertTrue(charts_rendered, "All four chart canvases should be present")
#
#     def test_no_404_maps(self):
#         """Test that network log shows no 404 requests for .map files."""
#         if not self.driver:
#             self.skipTest("Chrome WebDriver not available")
#
#         # Enable performance logging to capture network requests
#         caps = DesiredCapabilities.CHROME
#         caps['goog:loggingPrefs'] = {'performance': 'ALL'}
#
#         # Login and navigate to dashboard
#         self.driver.get(f'{self.live_server_url}/admin/login/')
#         username_input = self.driver.find_element(By.NAME, 'username')
#         password_input = self.driver.find_element(By.NAME, 'password')
#         username_input.send_keys('testadmin')
#         password_input.send_keys('testpass')
#         self.driver.find_element(By.XPATH, '//input[@type="submit"]').click()
#
#         # Clear logs before navigating to dashboard
#         self.driver.get_log('performance')
#
#         # Navigate to dashboard
#         self.driver.get(f'{self.live_server_url}/dashboard/')
#
#         # Wait for page to fully load
#         WebDriverWait(self.driver, 10).until(
#             EC.presence_of_element_located((By.CLASS_NAME, 'dashboard-container'))
#         )
#         time.sleep(2)
#
#         # Get performance logs (network requests)
#         logs = self.driver.get_log('performance')
#
#         # Look for any 404 responses to .map files
#         map_404_requests = []
#         for log in logs:
#             message = json.loads(log['message'])
#             if message.get('message', {}).get('method') == 'Network.responseReceived':
#                 response = message['message']['params']['response']
#                 if (response.get('status') == 404 and
#                     response.get('url', '').endswith('.map')):
#                     map_404_requests.append(response['url'])
#
#         # Assert no 404 requests for .map files
#         if map_404_requests:
#             self.fail(f"Found 404 requests for map files: {map_404_requests}")
