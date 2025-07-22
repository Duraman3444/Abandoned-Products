#!/usr/bin/env python3
"""
Authenticated Dashboard Testing
Tests dashboard after proper login
"""

import requests
import re
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"
LOGIN_URL = urljoin(BASE_URL, "/admin/login/")
DASHBOARD_URL = urljoin(BASE_URL, "/dashboard/")

def login_and_get_dashboard():
    """Login properly and get the dashboard content"""
    session = requests.Session()
    
    try:
        print("🔐 Attempting to login to admin...")
        
        # Get login page first
        login_page = session.get(LOGIN_URL)
        print(f"Login page status: {login_page.status_code}")
        
        # Extract CSRF token
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        if not csrf_token:
            print("❌ Could not find CSRF token")
            return None
        
        print(f"✅ CSRF token found: {csrf_token[:20]}...")
        
        # Perform login
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token,
            'next': '/dashboard/',
        }
        
        headers = {
            'Referer': LOGIN_URL,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        login_response = session.post(LOGIN_URL, data=login_data, headers=headers, allow_redirects=True)
        print(f"Login response status: {login_response.status_code}")
        print(f"Final URL after login: {login_response.url}")
        
        # Now try to access dashboard
        dashboard_response = session.get(DASHBOARD_URL)
        print(f"Dashboard access status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("✅ Successfully accessed dashboard!")
            return analyze_authenticated_dashboard(dashboard_response.text)
        else:
            print(f"❌ Dashboard access failed: {dashboard_response.status_code}")
            print(f"Response content sample: {dashboard_response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return None

def analyze_authenticated_dashboard(html_content):
    """Analyze the actual dashboard content after successful login"""
    print("\n" + "="*60)
    print("📊 AUTHENTICATED DASHBOARD ANALYSIS")
    print("="*60)
    
    # Extract title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "No title found"
    print(f"\n📄 Page Title: {title}")
    
    # Check if this is actually the dashboard or still login page
    if 'login' in title.lower() or 'log in' in html_content.lower():
        print("❌ Still on login page - authentication may have failed")
        return None
    
    # Analyze dashboard structure
    print(f"\n🏗️ Page Structure:")
    structure_counts = {
        'Total characters': len(html_content),
        'Div elements': len(re.findall(r'<div', html_content, re.IGNORECASE)),
        'Script tags': len(re.findall(r'<script', html_content, re.IGNORECASE)),
        'Style/CSS references': len(re.findall(r'<link.*\.css|<style', html_content, re.IGNORECASE)),
        'Form elements': len(re.findall(r'<form', html_content, re.IGNORECASE)),
        'Table elements': len(re.findall(r'<table', html_content, re.IGNORECASE)),
        'Button elements': len(re.findall(r'<button', html_content, re.IGNORECASE)),
        'Input elements': len(re.findall(r'<input', html_content, re.IGNORECASE)),
    }
    
    for item, count in structure_counts.items():
        print(f"  • {item}: {count}")
    
    # Look for chart libraries
    print(f"\n📈 Chart Technology Detection:")
    chart_libraries = {
        'Chart.js': bool(re.search(r'chart\.js|chartjs', html_content, re.IGNORECASE)),
        'D3.js': bool(re.search(r'd3\.js|d3\.min\.js', html_content, re.IGNORECASE)),
        'Plotly': bool(re.search(r'plotly', html_content, re.IGNORECASE)),
        'ApexCharts': bool(re.search(r'apexcharts', html_content, re.IGNORECASE)),
        'Canvas elements': bool(re.search(r'<canvas', html_content, re.IGNORECASE)),
        'SVG elements': bool(re.search(r'<svg', html_content, re.IGNORECASE)),
    }
    
    for library, found in chart_libraries.items():
        status = "✅ Found" if found else "❌ Not found"
        print(f"  • {library}: {status}")
    
    # Look for dashboard-specific elements
    print(f"\n🎯 Dashboard Features:")
    dashboard_features = {
        'KPI/Metrics cards': bool(re.search(r'class="[^"]*(?:kpi|metric|stat|card)[^"]*"', html_content, re.IGNORECASE)),
        'Chart containers': bool(re.search(r'class="[^"]*(?:chart|graph)[^"]*"|id="[^"]*(?:chart|graph)[^"]*"', html_content, re.IGNORECASE)),
        'Export buttons': bool(re.search(r'export|download|csv', html_content, re.IGNORECASE)),
        'Refresh functionality': bool(re.search(r'refresh|reload', html_content, re.IGNORECASE)),
        'Dark mode toggle': bool(re.search(r'dark.?mode|theme.?toggle', html_content, re.IGNORECASE)),
        'Navigation sidebar': bool(re.search(r'sidebar|nav-sidebar', html_content, re.IGNORECASE)),
        'Responsive classes': bool(re.search(r'col-|row-|container-|responsive', html_content, re.IGNORECASE)),
        'Bootstrap': bool(re.search(r'bootstrap', html_content, re.IGNORECASE)),
    }
    
    for feature, found in dashboard_features.items():
        status = "✅ Available" if found else "❌ Not available"
        print(f"  • {feature}: {status}")
    
    # Extract visible text content
    print(f"\n📝 Dashboard Content Analysis:")
    
    # Remove scripts and styles for content analysis
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract text
    text_content = re.sub(r'<[^>]+>', ' ', clean_html)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Look for numbers that might be KPIs
    numbers = re.findall(r'\b\d+(?:,\d{3})*\b', text_content)
    if numbers:
        print(f"  • Numeric values (potential KPIs): {len(numbers)} found")
        print(f"    Examples: {', '.join(numbers[:10])}")
    
    # Extract meaningful words
    words = [word for word in text_content.split() if len(word) > 3]
    if words:
        print(f"  • Content words: {len(words)} total")
        print(f"  • Sample content: {' '.join(words[:30])}...")
    
    # Look for specific dashboard sections
    print(f"\n🔍 Dashboard Sections:")
    
    # Try to identify main content sections
    sections = re.findall(r'<div[^>]*class="[^"]*(?:dashboard|content|main)[^"]*"[^>]*>(.*?)</div>', html_content, re.DOTALL | re.IGNORECASE)
    if sections:
        print(f"  • Found {len(sections)} main content sections")
    
    # Look for specific IDs that suggest dashboard content
    dashboard_ids = re.findall(r'id="([^"]*(?:dashboard|chart|kpi|metric)[^"]*)"', html_content, re.IGNORECASE)
    if dashboard_ids:
        print(f"  • Dashboard element IDs: {', '.join(dashboard_ids)}")
    
    # Show raw HTML sample
    print(f"\n📄 HTML Sample (first 1500 characters):")
    print("-" * 50)
    print(html_content[:1500])
    if len(html_content) > 1500:
        print("... (truncated)")
    
    return {
        'title': title,
        'html_length': len(html_content),
        'chart_libraries': chart_libraries,
        'dashboard_features': dashboard_features,
        'content_words': len(words) if 'words' in locals() else 0,
        'numeric_values': len(numbers) if 'numbers' in locals() else 0,
    }

if __name__ == "__main__":
    result = login_and_get_dashboard()
    if result:
        print(f"\n✅ Dashboard analysis completed successfully")
    else:
        print(f"\n❌ Could not analyze dashboard")
