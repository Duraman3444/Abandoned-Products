from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings
import re


class DashboardStyleTests(TestCase):
    """Test cases for dashboard dark theme styling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststaff',
            password='testpass123',
            is_staff=True
        )
        
    def test_dark_background(self):
        """Test that dashboard body has dark background color."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check that the response contains the dark theme class
        self.assertContains(response, 'dashboard-dark')
        self.assertContains(response, 'dashboard-container')
        
    def test_primary_button_class(self):
        """Test that Download CSV button has btn-primary class."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for btn-primary class on download button
        self.assertContains(response, 'btn-primary')
        self.assertContains(response, 'Download CSV')
        
    def test_chart_ticks_color(self):
        """Test that Chart config uses correct text color."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for the dark theme Chart.js color configuration
        self.assertContains(response, "Chart.defaults.color = '#E6EDF3'")
        self.assertContains(response, "color: '#E6EDF3'")
        
    def test_dashboard_css_loaded(self):
        """Test that dashboard.css is properly loaded."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for CSS file inclusion
        self.assertContains(response, 'css/dashboard.css')
        
    def test_stat_cards_styling(self):
        """Test that stat cards use dark theme classes."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for stat card classes
        self.assertContains(response, 'stat-card')
        self.assertContains(response, 'stat-icon')
        self.assertContains(response, 'stat-value')
        
    def test_chart_dark_theme_config(self):
        """Test that charts are configured with dark theme colors."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for dark theme grid colors
        self.assertContains(response, "rgba(255, 255, 255, 0.1)")
        
    def test_responsive_grid_classes(self):
        """Test that responsive grid classes are present."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for responsive grid classes
        self.assertContains(response, 'stats-grid')
        self.assertContains(response, 'charts-grid')
        
    def test_accessibility_features(self):
        """Test that accessibility features are present."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for ARIA labels and semantic HTML
        self.assertContains(response, 'aria-label="Breadcrumb"')
        
    def test_button_variants(self):
        """Test that all button variants are present."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for different button classes
        self.assertContains(response, 'btn-primary')
        self.assertContains(response, 'btn-secondary')
        self.assertContains(response, 'btn-tertiary')
        
    def test_dark_theme_override(self):
        """Test that dark theme JavaScript override is present."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for dark theme body class override
        self.assertContains(response, "document.body.className = 'dashboard-dark'")
        
        # Check that dashboard uses dark theme classes
        self.assertContains(response, 'dashboard-container')
        self.assertContains(response, 'stat-card')
        self.assertContains(response, 'chart-card')


class DashboardResponsivenessTests(TestCase):
    """Test cases for dashboard responsiveness."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststaff',
            password='testpass123',
            is_staff=True
        )
        
    def test_mobile_viewport_meta(self):
        """Test that mobile viewport meta tag is present."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for mobile viewport meta tag in base template
        self.assertContains(response, 'name="viewport"')
        
    def test_responsive_css_classes(self):
        """Test that responsive CSS classes are used."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for CSS grid and flexbox responsive classes
        self.assertContains(response, 'dashboard-content')
        self.assertContains(response, 'dashboard-actions')


class DashboardPerformanceTests(TestCase):
    """Test cases for dashboard performance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststaff',
            password='testpass123',
            is_staff=True
        )
        
    def test_css_minification_ready(self):
        """Test that CSS is structured for minification."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # CSS should be loaded from static files
        self.assertContains(response, 'static/css/dashboard.css')
        
    def test_chart_lazy_loading(self):
        """Test that charts are initialized properly."""
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for chart initialization function
        self.assertContains(response, 'initializeCharts()')
        self.assertContains(response, "DOMContentLoaded")
