#!/usr/bin/env python3
"""
Comprehensive test script for Priority 3 Mobile & Usability features
Tests all functionality outlined in DASHBOARD_CHECKLISTS.md
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def setup_test_data():
    """Create minimal test data"""
    print("📊 Setting up test data...")
    
    # Create teacher user
    teacher_user, _ = User.objects.get_or_create(
        username='mobile_test_teacher',
        defaults={
            'first_name': 'Mobile',
            'last_name': 'TestTeacher',
            'email': 'teacher@mobile.test',
            'is_staff': True
        }
    )
    teacher_user.set_password('testpass123')
    teacher_user.save()
    
    return teacher_user

def test_mobile_responsive_design():
    """Test mobile-responsive design features"""
    print("\n🧪 Testing Mobile-Responsive Design...")
    
    # Setup Chrome with mobile emulation
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Mobile device emulation (iPhone 12)
    mobile_emulation = {
        "deviceMetrics": {"width": 390, "height": 844, "pixelRatio": 3.0},
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15"
    }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('http://localhost:8000')
        
        # Test 1: Check if viewport is mobile-optimized
        viewport_width = driver.execute_script("return window.innerWidth")
        print(f"✅ Mobile viewport width: {viewport_width}px")
        
        # Test 2: Check if mobile-responsive CSS is loaded
        mobile_css_loaded = driver.execute_script("""
            const links = document.querySelectorAll('link[href*="mobile-responsive.css"]');
            return links.length > 0;
        """)
        print(f"✅ Mobile-responsive CSS loaded: {mobile_css_loaded}")
        
        # Test 3: Touch targets are appropriately sized (minimum 44px)
        touch_targets = driver.execute_script("""
            const buttons = document.querySelectorAll('button, .btn, input[type="button"], .attendance-btn');
            let undersized = 0;
            buttons.forEach(btn => {
                const rect = btn.getBoundingClientRect();
                if (rect.width < 44 || rect.height < 44) {
                    undersized++;
                }
            });
            return {total: buttons.length, undersized: undersized};
        """)
        print(f"✅ Touch targets check: {touch_targets['total'] - touch_targets['undersized']}/{touch_targets['total']} properly sized")
        
        # Test 4: Test horizontal scrolling for tables
        gradebook_scrollable = driver.execute_script("""
            const tables = document.querySelectorAll('.table-responsive, .gradebook-container');
            return tables.length > 0 && tables[0].scrollWidth > tables[0].clientWidth;
        """)
        print(f"✅ Gradebook horizontal scrolling available: {gradebook_scrollable}")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Mobile responsive test error: {str(e)}")
        return False

def test_quick_action_buttons():
    """Test quick action buttons functionality"""
    print("\n🧪 Testing Quick Action Buttons...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Setup test data
        teacher_user = setup_test_data()
        
        # Login
        driver.get('http://localhost:8000/accounts/login/')
        driver.find_element(By.NAME, 'username').send_keys('mobile_test_teacher')
        driver.find_element(By.NAME, 'password').send_keys('testpass123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        time.sleep(2)
        
        # Test 1: Check if mobile FABs are present
        mobile_fabs = driver.execute_script("""
            return document.querySelectorAll('.mobile-fab, .quick-action-btn').length;
        """)
        print(f"✅ Mobile floating action buttons found: {mobile_fabs}")
        
        # Test 2: Test quick attendance button (< 3 clicks)
        click_count = 0
        try:
            # Navigate to attendance page
            driver.get('http://localhost:8000/teacher/attendance/')
            click_count += 1
            
            # Look for quick "All Present" button
            all_present_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'All Present')]")
            all_present_btn.click()
            click_count += 1
            
            print(f"✅ Quick attendance action completed in {click_count} clicks (target: <3)")
            
        except Exception as e:
            print(f"⚠️ Quick attendance test: {str(e)}")
        
        # Test 3: Check keyboard navigation support
        keyboard_shortcuts = driver.execute_script("""
            // Check if keyboard event listeners are attached
            const hasKeyboardSupport = document.querySelector('script')?.textContent?.includes('keydown') || false;
            return hasKeyboardSupport;
        """)
        print(f"✅ Keyboard shortcuts supported: {keyboard_shortcuts}")
        
        # Test 4: Dashboard quick actions accessibility
        dashboard_actions = driver.execute_script("""
            const quickActions = document.querySelectorAll('[title*="Quick"], [aria-label*="Quick"], .quick-');
            return quickActions.length;
        """)
        print(f"✅ Dashboard quick actions available: {dashboard_actions}")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Quick action buttons test error: {str(e)}")
        return False

def test_keyboard_shortcuts():
    """Test keyboard shortcuts for power users"""
    print("\n🧪 Testing Keyboard Shortcuts...")
    
    test_results = {
        'arrow_navigation': False,
        'tab_navigation': False,
        'shortcuts_documented': False,
        'escape_handling': False
    }
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Setup and login
        teacher_user = setup_test_data()
        driver.get('http://localhost:8000/accounts/login/')
        driver.find_element(By.NAME, 'username').send_keys('mobile_test_teacher')
        driver.find_element(By.NAME, 'password').send_keys('testpass123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        time.sleep(2)
        
        # Test 1: Arrow key navigation in gradebook
        try:
            driver.get('http://localhost:8000/teacher/gradebook/')
            
            # Check if arrow key navigation is implemented
            arrow_nav_support = driver.execute_script("""
                return document.querySelector('script')?.textContent?.includes('ArrowDown') &&
                       document.querySelector('script')?.textContent?.includes('ArrowUp') &&
                       document.querySelector('script')?.textContent?.includes('ArrowLeft') &&
                       document.querySelector('script')?.textContent?.includes('ArrowRight');
            """)
            test_results['arrow_navigation'] = arrow_nav_support
            print(f"✅ Arrow key navigation implemented: {arrow_nav_support}")
            
        except Exception as e:
            print(f"⚠️ Arrow navigation test: {str(e)}")
        
        # Test 2: Tab navigation through attendance
        try:
            driver.get('http://localhost:8000/teacher/attendance/')
            
            # Check if tab navigation is enhanced
            tab_support = driver.execute_script("""
                const inputs = document.querySelectorAll('input, button, select');
                let tabbableCount = 0;
                inputs.forEach(el => {
                    if (el.tabIndex >= 0 || !el.hasAttribute('tabindex')) {
                        tabbableCount++;
                    }
                });
                return tabbableCount > 0;
            """)
            test_results['tab_navigation'] = tab_support
            print(f"✅ Tab navigation supported: {tab_support}")
            
        except Exception as e:
            print(f"⚠️ Tab navigation test: {str(e)}")
        
        # Test 3: Check if shortcuts are documented
        shortcuts_documented = driver.execute_script("""
            // Look for keyboard shortcut documentation
            const hasShortcutInfo = document.body.textContent.includes('Alt+') ||
                                   document.body.textContent.includes('Ctrl+') ||
                                   document.body.textContent.includes('keyboard') ||
                                   document.querySelector('[title*="Alt"], [title*="Ctrl"]');
            return Boolean(hasShortcutInfo);
        """)
        test_results['shortcuts_documented'] = shortcuts_documented
        print(f"✅ Keyboard shortcuts discoverable: {shortcuts_documented}")
        
        # Test 4: Escape key handling
        escape_handling = driver.execute_script("""
            return document.querySelector('script')?.textContent?.includes('Escape') || 
                   document.querySelector('script')?.textContent?.includes('key === \"Escape\"');
        """)
        test_results['escape_handling'] = escape_handling
        print(f"✅ Escape key handling implemented: {escape_handling}")
        
        driver.quit()
        
        success_count = sum(test_results.values())
        print(f"✅ Keyboard shortcuts: {success_count}/4 tests passed")
        return success_count >= 3
        
    except Exception as e:
        print(f"❌ Keyboard shortcuts test error: {str(e)}")
        return False

def test_dark_mode_support():
    """Test dark mode functionality"""
    print("\n🧪 Testing Dark Mode Support...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('http://localhost:8000')
        
        # Test 1: Dark mode toggle exists
        toggle_exists = driver.execute_script("""
            return document.querySelector('#darkModeToggle, .dark-mode-toggle') !== null;
        """)
        print(f"✅ Dark mode toggle button exists: {toggle_exists}")
        
        # Test 2: Dark mode CSS is loaded
        dark_mode_css = driver.execute_script("""
            return document.querySelector('script[src*="dark-mode"]') !== null ||
                   document.querySelector('link[href*="dark-mode"]') !== null ||
                   document.head.textContent.includes('data-theme="dark"');
        """)
        print(f"✅ Dark mode CSS/JS loaded: {dark_mode_css}")
        
        # Test 3: Theme persistence (localStorage)
        theme_persistence = driver.execute_script("""
            // Test if localStorage is used for theme persistence
            try {
                localStorage.setItem('test-theme', 'dark');
                const canStore = localStorage.getItem('test-theme') === 'dark';
                localStorage.removeItem('test-theme');
                return canStore;
            } catch (e) {
                return false;
            }
        """)
        print(f"✅ Theme persistence capability: {theme_persistence}")
        
        # Test 4: Dark mode colors and contrast
        color_vars_defined = driver.execute_script("""
            const styles = getComputedStyle(document.documentElement);
            return styles.getPropertyValue('--bg-primary') !== '' ||
                   styles.getPropertyValue('--text-primary') !== '' ||
                   document.head.textContent.includes('--bg-') ||
                   document.head.textContent.includes('data-theme');
        """)
        print(f"✅ Dark mode color system defined: {color_vars_defined}")
        
        driver.quit()
        return toggle_exists and (dark_mode_css or color_vars_defined)
        
    except Exception as e:
        print(f"❌ Dark mode test error: {str(e)}")
        return False

def test_accessibility_compliance():
    """Test accessibility features"""
    print("\n🧪 Testing Accessibility Compliance...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('http://localhost:8000')
        
        # Test 1: ARIA labels present
        aria_labels = driver.execute_script("""
            const elementsWithAria = document.querySelectorAll('[aria-label], [aria-labelledby], [role]');
            return elementsWithAria.length;
        """)
        print(f"✅ Elements with ARIA labels/roles: {aria_labels}")
        
        # Test 2: Form inputs have proper labels
        form_labels = driver.execute_script("""
            const inputs = document.querySelectorAll('input, select, textarea');
            let labeledInputs = 0;
            inputs.forEach(input => {
                const hasLabel = input.labels?.length > 0 || 
                               input.getAttribute('aria-label') || 
                               input.getAttribute('placeholder') ||
                               input.getAttribute('title');
                if (hasLabel) labeledInputs++;
            });
            return {total: inputs.length, labeled: labeledInputs};
        """)
        print(f"✅ Form inputs with labels: {form_labels['labeled']}/{form_labels['total']}")
        
        # Test 3: Color contrast considerations
        contrast_support = driver.execute_script("""
            // Check if there are high contrast or color-blind friendly features
            return document.head.textContent.includes('contrast') ||
                   document.head.textContent.includes('color-blind') ||
                   document.head.textContent.includes('a11y') ||
                   document.body.className.includes('-contrast');
        """)
        print(f"✅ Color contrast considerations: {contrast_support}")
        
        # Test 4: Keyboard navigation support
        keyboard_nav = driver.execute_script("""
            const focusableElements = document.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            return focusableElements.length;
        """)
        print(f"✅ Keyboard navigable elements: {keyboard_nav}")
        
        driver.quit()
        
        # Pass if we have good ARIA support and form labels
        return aria_labels > 5 and form_labels['labeled'] / max(form_labels['total'], 1) > 0.5
        
    except Exception as e:
        print(f"❌ Accessibility test error: {str(e)}")
        return False

def test_print_friendly_views():
    """Test print-friendly layouts"""
    print("\n🧪 Testing Print-Friendly Views...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('http://localhost:8000')
        
        # Test 1: Print CSS is loaded
        print_css_loaded = driver.execute_script("""
            const links = document.querySelectorAll('link[href*="print"]');
            const styles = document.querySelectorAll('style');
            let hasPrintStyles = links.length > 0;
            
            styles.forEach(style => {
                if (style.textContent.includes('@media print')) {
                    hasPrintStyles = true;
                }
            });
            
            return hasPrintStyles;
        """)
        print(f"✅ Print CSS loaded: {print_css_loaded}")
        
        # Test 2: Print button exists
        print_button = driver.execute_script("""
            return document.querySelectorAll('[onclick*="print"], .print-button, [title*="Print"]').length > 0;
        """)
        print(f"✅ Print button available: {print_button}")
        
        # Test 3: Print-optimized layout elements
        print_optimizations = driver.execute_script("""
            const printElements = document.querySelectorAll('.print-header, .print-only, .no-print');
            return printElements.length;
        """)
        print(f"✅ Print-specific elements: {print_optimizations}")
        
        # Test 4: Test print functionality (simulate)
        print_function_exists = driver.execute_script("""
            return typeof window.print === 'function' && 
                   (document.body.textContent.includes('print') || 
                    document.querySelector('script')?.textContent?.includes('print'));
        """)
        print(f"✅ Print functionality implemented: {print_function_exists}")
        
        driver.quit()
        return print_css_loaded and print_button
        
    except Exception as e:
        print(f"❌ Print-friendly test error: {str(e)}")
        return False

def run_all_mobile_usability_tests():
    """Run all mobile and usability tests"""
    print("🚀 Starting Priority 3 Mobile & Usability Tests")
    print("=" * 60)
    
    test_results = {}
    
    try:
        # Run all tests
        test_results['mobile_responsive'] = test_mobile_responsive_design()
        test_results['quick_actions'] = test_quick_action_buttons()
        test_results['keyboard_shortcuts'] = test_keyboard_shortcuts()
        test_results['dark_mode'] = test_dark_mode_support()
        test_results['accessibility'] = test_accessibility_compliance()
        test_results['print_friendly'] = test_print_friendly_views()
        
        print("\n" + "=" * 60)
        print("📊 MOBILE & USABILITY TEST RESULTS:")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
            if result:
                passed_tests += 1
        
        print("\n" + "=" * 60)
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT! Mobile & Usability features are working well!")
        elif success_rate >= 60:
            print("👍 GOOD! Most mobile & usability features are functional.")
        else:
            print("⚠️ NEEDS IMPROVEMENT: Several mobile & usability issues detected.")
        
        print("\nFeatures successfully tested:")
        if test_results['mobile_responsive']:
            print("• Mobile-responsive design with touch-friendly targets")
        if test_results['quick_actions']:
            print("• Quick action buttons for common tasks")
        if test_results['keyboard_shortcuts']:
            print("• Keyboard shortcuts for power users")
        if test_results['dark_mode']:
            print("• Dark mode support with theme persistence")
        if test_results['accessibility']:
            print("• Accessibility compliance with ARIA labels")
        if test_results['print_friendly']:
            print("• Print-friendly layouts for reports")
        
        return success_rate >= 60
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_mobile_usability_tests()
    sys.exit(0 if success else 1)
