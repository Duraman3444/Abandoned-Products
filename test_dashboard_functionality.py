#!/usr/bin/env python3
"""
Analytics Dashboard Testing Script
Tests all dashboard features including charts, CSV export, and UI elements.
"""

import requests
import time
import json
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:8000"
DASHBOARD_URL = urljoin(BASE_URL, "/dashboard/")
LOGIN_URL = urljoin(BASE_URL, "/admin/login/")

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

def test_dashboard_access():
    """Test dashboard accessibility and authentication"""
    print("🔍 Testing Dashboard Access...")
    
    session = requests.Session()
    
    try:
        # First, try to access dashboard directly
        response = session.get(DASHBOARD_URL)
        print(f"Dashboard direct access: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard accessible without authentication")
            return session, True
        elif response.status_code == 302 or response.status_code == 403:
            print("🔐 Dashboard requires authentication, attempting login...")
            return login_and_access_dashboard(session)
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return session, False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on localhost:8000?")
        return None, False
    except Exception as e:
        print(f"❌ Error accessing dashboard: {e}")
        return None, False

def login_and_access_dashboard(session):
    """Login with admin credentials and access dashboard"""
    try:
        # Get login page to get CSRF token
        login_response = session.get(LOGIN_URL)
        if login_response.status_code != 200:
            print(f"❌ Cannot access login page: {login_response.status_code}")
            return session, False
        
        # Extract CSRF token
        csrf_token = None
        if 'csrfmiddlewaretoken' in login_response.text:
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        # Login with credentials
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'next': '/dashboard/',
        }
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        login_post_response = session.post(LOGIN_URL, data=login_data)
        
        # Try dashboard again
        dashboard_response = session.get(DASHBOARD_URL)
        if dashboard_response.status_code == 200:
            print("✅ Successfully logged in and accessed dashboard")
            return session, True
        else:
            print(f"❌ Login failed or dashboard still inaccessible: {dashboard_response.status_code}")
            return session, False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return session, False

def analyze_dashboard_content(session):
    """Analyze dashboard HTML content for charts and features"""
    print("\n📊 Analyzing Dashboard Content...")
    
    try:
        response = session.get(DASHBOARD_URL)
        html_content = response.text
        
        # Check for common chart libraries and elements
        chart_indicators = {
            'Chart.js': 'chart.js' in html_content.lower() or 'chartjs' in html_content.lower(),
            'D3.js': 'd3.js' in html_content.lower() or 'd3.' in html_content,
            'Plotly': 'plotly' in html_content.lower(),
            'Canvas elements': '<canvas' in html_content,
            'SVG elements': '<svg' in html_content,
        }
        
        # Check for dashboard features
        dashboard_features = {
            'KPI metrics': any(keyword in html_content.lower() for keyword in ['kpi', 'metric', 'stat', 'count']),
            'CSV export': any(keyword in html_content.lower() for keyword in ['csv', 'export', 'download']),
            'Dark mode': any(keyword in html_content.lower() for keyword in ['dark-mode', 'theme-toggle', 'dark']),
            'Auto-refresh': any(keyword in html_content.lower() for keyword in ['refresh', 'auto-update', 'setinterval']),
            'Sidebar navigation': any(keyword in html_content.lower() for keyword in ['sidebar', 'nav', 'menu']),
            'Responsive design': any(keyword in html_content.lower() for keyword in ['responsive', 'mobile', 'col-', 'bootstrap']),
        }
        
        print("\n📈 Chart Technologies Detected:")
        for tech, found in chart_indicators.items():
            status = "✅ Found" if found else "❌ Not found"
            print(f"  {tech}: {status}")
        
        print("\n🎯 Dashboard Features Detected:")
        for feature, found in dashboard_features.items():
            status = "✅ Found" if found else "❌ Not found"
            print(f"  {feature}: {status}")
        
        # Look for specific chart containers or IDs
        print("\n🎨 Chart Container Analysis:")
        chart_containers = []
        import re
        
        # Look for common chart container patterns
        chart_patterns = [
            r'id=["\']([^"\']*chart[^"\']*)["\']',
            r'class=["\']([^"\']*chart[^"\']*)["\']',
            r'canvas.*id=["\']([^"\']*)["\']',
            r'<div[^>]*data-chart[^>]*>',
        ]
        
        for pattern in chart_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            chart_containers.extend(matches)
        
        if chart_containers:
            print(f"  Found {len(chart_containers)} potential chart containers:")
            for container in set(chart_containers[:10]):  # Show first 10 unique
                print(f"    - {container}")
        else:
            print("  No chart containers detected")
        
        return html_content, chart_indicators, dashboard_features
        
    except Exception as e:
        print(f"❌ Error analyzing content: {e}")
        return None, {}, {}

def test_csv_export_endpoints(session):
    """Test for CSV export functionality"""
    print("\n📥 Testing CSV Export Functionality...")
    
    # Common CSV export endpoint patterns
    csv_endpoints = [
        '/dashboard/export/csv/',
        '/dashboard/csv/',
        '/export/csv/',
        '/api/dashboard/export/',
        '/dashboard/data/csv/',
        '/dashboard/download/',
    ]
    
    csv_found = False
    working_endpoints = []
    
    for endpoint in csv_endpoints:
        try:
            url = urljoin(BASE_URL, endpoint)
            response = session.get(url)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'csv' in content_type or 'text/csv' in content_type:
                    print(f"✅ CSV endpoint found: {endpoint}")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {len(response.content)} bytes")
                    working_endpoints.append(endpoint)
                    csv_found = True
                elif response.status_code == 200:
                    print(f"🔍 Endpoint exists but may not be CSV: {endpoint} (status: {response.status_code})")
            elif response.status_code == 404:
                continue  # Expected for non-existent endpoints
            else:
                print(f"🔍 Endpoint response: {endpoint} (status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")
    
    if not csv_found:
        print("❌ No CSV export endpoints found in common locations")
    
    return working_endpoints

def test_api_endpoints(session):
    """Test for API endpoints that might provide chart data"""
    print("\n🔌 Testing API Endpoints...")
    
    api_endpoints = [
        '/api/dashboard/',
        '/api/analytics/',
        '/api/charts/',
        '/dashboard/api/',
        '/dashboard/data/',
        '/dashboard/ajax/',
    ]
    
    working_apis = []
    
    for endpoint in api_endpoints:
        try:
            url = urljoin(BASE_URL, endpoint)
            response = session.get(url)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"✅ JSON API found: {endpoint}")
                        print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'List data'}")
                        working_apis.append(endpoint)
                    except:
                        print(f"🔍 Endpoint exists but response not JSON: {endpoint}")
                else:
                    print(f"🔍 Endpoint exists: {endpoint} (Content-Type: {content_type})")
                    
        except Exception as e:
            print(f"❌ Error testing API {endpoint}: {e}")
    
    return working_apis

def generate_report(chart_indicators, dashboard_features, csv_endpoints, api_endpoints, html_content):
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("📋 ANALYTICS DASHBOARD TEST REPORT")
    print("="*60)
    
    print(f"\n🕐 Test Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Dashboard URL: {DASHBOARD_URL}")
    print(f"🔐 Authentication: admin/admin123")
    
    print(f"\n📊 CHART TECHNOLOGIES SUMMARY:")
    for tech, found in chart_indicators.items():
        status = "DETECTED" if found else "NOT FOUND"
        print(f"  • {tech}: {status}")
    
    print(f"\n🎯 DASHBOARD FEATURES SUMMARY:")
    for feature, found in dashboard_features.items():
        status = "AVAILABLE" if found else "NOT AVAILABLE"
        print(f"  • {feature}: {status}")
    
    print(f"\n📥 CSV EXPORT STATUS:")
    if csv_endpoints:
        print(f"  ✅ CSV export functionality found ({len(csv_endpoints)} endpoints)")
        for endpoint in csv_endpoints:
            print(f"    - {endpoint}")
    else:
        print(f"  ❌ No CSV export functionality detected")
    
    print(f"\n🔌 API ENDPOINTS:")
    if api_endpoints:
        print(f"  ✅ API endpoints found ({len(api_endpoints)} endpoints)")
        for endpoint in api_endpoints:
            print(f"    - {endpoint}")
    else:
        print(f"  ❌ No API endpoints detected")
    
    # Performance and technical assessment
    print(f"\n⚡ TECHNICAL ASSESSMENT:")
    
    # Count elements for performance assessment
    if html_content:
        script_count = html_content.count('<script')
        style_count = html_content.count('<style') + html_content.count('.css')
        html_size = len(html_content)
        
        print(f"  • Page size: {html_size:,} characters")
        print(f"  • Script tags: {script_count}")
        print(f"  • Stylesheets: {style_count}")
        
        if html_size > 500000:
            print(f"    ⚠️  Large page size may affect performance")
        if script_count > 20:
            print(f"    ⚠️  High script count may affect load times")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    missing_features = [feature for feature, found in dashboard_features.items() if not found]
    if missing_features:
        print(f"  📝 Consider implementing:")
        for feature in missing_features:
            print(f"    - {feature}")
    
    if not csv_endpoints:
        print(f"  📝 Add CSV export functionality for data analysis")
    
    if not any(chart_indicators.values()):
        print(f"  📝 No chart libraries detected - verify chart implementation")
    
    print(f"\n✅ TEST COMPLETED")
    print("="*60)

def main():
    """Main testing function"""
    print("🚀 Starting Analytics Dashboard Test Suite")
    print("="*60)
    
    # Test dashboard access
    session, access_success = test_dashboard_access()
    
    if not access_success or not session:
        print("\n❌ Cannot access dashboard. Ending tests.")
        return
    
    # Analyze dashboard content
    html_content, chart_indicators, dashboard_features = analyze_dashboard_content(session)
    
    # Test CSV export
    csv_endpoints = test_csv_export_endpoints(session)
    
    # Test API endpoints
    api_endpoints = test_api_endpoints(session)
    
    # Generate comprehensive report
    generate_report(chart_indicators, dashboard_features, csv_endpoints, api_endpoints, html_content)

if __name__ == "__main__":
    main()
