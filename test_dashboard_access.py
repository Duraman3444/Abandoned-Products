#!/usr/bin/env python3
"""
Test dashboard access and check if charts are in the HTML.
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Setup Django
sys.path.append('./schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

def test_dashboard_access():
    """Test if we can access dashboard and find chart elements."""
    print("🔍 Testing dashboard access...")
    
    session = requests.Session()
    
    try:
        # Get login page to get CSRF token
        login_url = "http://localhost:8001/admin/login/"
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        # Login
        login_data = {
            'username': 'admin',
            'password': 'admin',
            'csrfmiddlewaretoken': csrf_token,
            'next': '/dashboard/'
        }
        
        login_response = session.post(login_url, data=login_data)
        print(f"📝 Login response status: {login_response.status_code}")
        
        # Access dashboard
        dashboard_url = "http://localhost:8001/dashboard/"
        dashboard_response = session.get(dashboard_url)
        print(f"📝 Dashboard response status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            content = dashboard_response.text
            
            # Check for chart canvas elements
            chart_ids = ['pipelineChart', 'documentsChart', 'statusChart', 'trendsChart']
            chart_names = ['Pipeline Progress', 'Document Completion', 'Status Distribution', 'Monthly Trends']
            
            found_charts = 0
            for chart_id, chart_name in zip(chart_ids, chart_names):
                if f'id="{chart_id}"' in content:
                    print(f"✅ Found {chart_name} canvas in HTML")
                    found_charts += 1
                else:
                    print(f"❌ Missing {chart_name} canvas in HTML")
            
            # Check for Chart.js
            if 'Chart.js' in content or 'chart.min.js' in content:
                print("✅ Chart.js library referenced in HTML")
            else:
                print("❌ Chart.js library not found in HTML")
            
            # Check for dashboard data
            if 'dashboardData' in content:
                print("✅ Dashboard data found in HTML")
            else:
                print("❌ Dashboard data not found in HTML")
            
            print(f"\n📊 Summary: {found_charts}/4 charts found in HTML")
            
            if found_charts == 4:
                print("🎉 All chart canvas elements are present in HTML!")
                
                # Check for the specific JS function calls
                if 'initializeCharts()' in content:
                    print("✅ Chart initialization function found")
                else:
                    print("❌ Chart initialization function not found")
                    
                return True
            else:
                print("💥 Some chart canvas elements are missing from HTML!")
                return False
                
        else:
            print(f"❌ Cannot access dashboard (status: {dashboard_response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_access()
    sys.exit(0 if success else 1)
