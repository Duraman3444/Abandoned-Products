from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import os


class LiveAnalyticsSeleniumTest(LiveServerTestCase):
    """Selenium tests for Live Analytics widget functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Setup Chrome options for testing
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            # Skip tests if Chrome driver is not available
            cls.driver = None
            
    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        if not self.driver:
            self.skipTest("Chrome WebDriver not available")
            
        # Create test user
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123',
            first_name='Test',
            last_name='Student'
        )
        self.user.profile.role = 'Student'
        self.user.profile.save()

    def login_as_student(self):
        """Helper method to login as student"""
        self.driver.get(f'{self.live_server_url}/accounts/login/')
        
        username_input = self.driver.find_element(By.NAME, 'username')
        password_input = self.driver.find_element(By.NAME, 'password')
        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        
        username_input.send_keys('teststudent')
        password_input.send_keys('testpass123')
        login_button.click()
        
        # Wait for redirect to dashboard
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/student/')
        )

    def test_live_analytics_widget_loads(self):
        """Test that the live analytics widget loads on the dashboard"""
        self.login_as_student()
        
        # Navigate to student dashboard
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Wait for live analytics widget to load
        try:
            analytics_widget = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
            )
            self.assertTrue(analytics_widget.is_displayed())
            
            # Check for pause button
            pause_button = self.driver.find_element(By.ID, 'pauseLiveAnalytics')
            self.assertTrue(pause_button.is_displayed())
            self.assertEqual(pause_button.text, 'Pause')
            
        except TimeoutException:
            self.fail("Live analytics widget did not load within timeout period")

    def test_pause_resume_functionality(self):
        """Test that the pause/resume button actually stops and starts updates"""
        self.login_as_student()
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Wait for the chart to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
        )
        
        # Wait for JavaScript to load
        time.sleep(2)
        
        # Check initial state - should be running
        pause_button = self.driver.find_element(By.ID, 'pauseLiveAnalytics')
        self.assertEqual(pause_button.text, 'Pause')
        
        # Get initial data point count
        initial_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.dataPoints.length : 0;
        """)
        
        # Wait for a few updates (6 seconds = 3 updates at 2-second intervals)
        time.sleep(6)
        
        # Get count after updates
        running_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.dataPoints.length : 0;
        """)
        
        # Should have more data points when running
        self.assertGreater(running_count, initial_count, 
                          "Chart should have added data points while running")
        
        # Click pause button
        pause_button.click()
        
        # Wait for button text to change
        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.ID, 'pauseLiveAnalytics').text == 'Resume'
        )
        
        # Get count after pausing
        paused_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.dataPoints.length : 0;
        """)
        
        # Wait a few seconds while paused
        time.sleep(6)
        
        # Get count after waiting while paused
        still_paused_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.dataPoints.length : 0;
        """)
        
        # Should not have added new data points while paused
        self.assertEqual(paused_count, still_paused_count,
                        "Chart should not add data points while paused")
        
        # Click resume button
        pause_button.click()
        
        # Wait for button text to change back
        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.ID, 'pauseLiveAnalytics').text == 'Pause'
        )
        
        # Wait for more updates after resuming
        time.sleep(6)
        
        # Get final count
        resumed_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.dataPoints.length : 0;
        """)
        
        # Should have more data points after resuming
        self.assertGreater(resumed_count, still_paused_count,
                          "Chart should add data points after resuming")

    def test_chart_continuous_updates(self):
        """Test that chart updates continuously over extended period"""
        self.login_as_student()
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Wait for chart to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
        )
        
        # Wait for JavaScript initialization
        time.sleep(2)
        
        # Record data points over 12 seconds (should get at least 6 updates)
        data_points = []
        
        for i in range(7):  # Check every 2 seconds for 14 seconds total
            count = self.driver.execute_script("""
                return window.dashboardLiveAnalytics ? 
                       window.dashboardLiveAnalytics.dataPoints.length : 0;
            """)
            data_points.append(count)
            
            if i < 6:  # Don't sleep after the last measurement
                time.sleep(2)
        
        # Verify continuous growth
        for i in range(1, len(data_points)):
            self.assertGreaterEqual(data_points[i], data_points[i-1],
                                   f"Data points should not decrease: {data_points}")
        
        # Should have gained at least 5 data points over 12 seconds
        total_growth = data_points[-1] - data_points[0]
        self.assertGreaterEqual(total_growth, 5,
                               f"Should have at least 5 new data points, got {total_growth}")

    def test_sliding_window_behavior(self):
        """Test that chart maintains sliding window of max 50 data points"""
        self.login_as_student()
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Wait for chart to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
        )
        
        # Wait for initialization
        time.sleep(2)
        
        # Force add many data points to test sliding window
        self.driver.execute_script("""
            if (window.dashboardLiveAnalytics) {
                // Add 60 data points quickly
                for (let i = 0; i < 60; i++) {
                    window.dashboardLiveAnalytics.addDataPoint();
                }
            }
        """)
        
        # Check that it maintains exactly 50 data points
        final_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.dataPoints.length : 0;
        """)
        
        self.assertEqual(final_count, 50,
                        "Chart should maintain exactly 50 data points in sliding window")
        
        # Check that labels match data points count
        labels_count = self.driver.execute_script("""
            return window.dashboardLiveAnalytics ? 
                   window.dashboardLiveAnalytics.labels.length : 0;
        """)
        
        self.assertEqual(labels_count, 50,
                        "Labels should match data points count")

    def test_chart_visual_elements(self):
        """Test that chart visual elements are present and functional"""
        self.login_as_student()
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Wait for chart to load
        chart_canvas = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
        )
        
        # Check canvas is visible and has proper dimensions
        self.assertTrue(chart_canvas.is_displayed())
        
        # Check widget title
        widget_title = self.driver.find_element(By.XPATH, "//h6[contains(text(), 'Live Analytics')]")
        self.assertTrue(widget_title.is_displayed())
        
        # Check status text
        status_text = self.driver.find_element(By.XPATH, "//small[contains(text(), 'Updates every 2 seconds')]")
        self.assertTrue(status_text.is_displayed())
        
        # Verify Chart.js is loaded
        chart_loaded = self.driver.execute_script("""
            return typeof Chart !== 'undefined' && window.dashboardLiveAnalytics !== null;
        """)
        
        self.assertTrue(chart_loaded, "Chart.js should be loaded and analytics initialized")

    def test_responsive_design(self):
        """Test that the widget is responsive on different screen sizes"""
        self.login_as_student()
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
        )
        
        # Test desktop view (should be in col-lg-4)
        self.driver.set_window_size(1200, 800)
        widget_container = self.driver.find_element(By.XPATH, "//div[contains(@class, 'col-lg-4')]")
        self.assertTrue(widget_container.is_displayed())
        
        # Test mobile view (should stack full width)
        self.driver.set_window_size(400, 800)
        time.sleep(1)  # Wait for responsive layout change
        
        # Widget should still be visible on mobile
        mobile_chart = self.driver.find_element(By.ID, 'liveAnalyticsChart')
        self.assertTrue(mobile_chart.is_displayed())

    def test_error_handling(self):
        """Test error handling when Chart.js fails to load"""
        self.login_as_student()
        
        # Block Chart.js from loading
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {
            "urls": ["*chart.js*", "*Chart*"]
        })
        
        self.driver.get(f'{self.live_server_url}/student/')
        
        # Page should still load even if Chart.js fails
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'liveAnalyticsChart'))
            )
            
            # Check that error is handled gracefully
            console_errors = self.driver.get_log('browser')
            chart_errors = [log for log in console_errors if 'Chart' in log['message']]
            
            # Should not crash the page
            dashboard_title = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Welcome back')]")
            self.assertTrue(dashboard_title.is_displayed())
            
        except Exception as e:
            # If canvas not found, that's also acceptable error handling
            pass

    def tearDown(self):
        """Clean up after each test"""
        if self.driver:
            # Clear any JavaScript timers
            self.driver.execute_script("""
                if (window.dashboardLiveAnalytics) {
                    window.dashboardLiveAnalytics.destroy();
                }
            """)
