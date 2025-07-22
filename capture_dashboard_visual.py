#!/usr/bin/env python3
"""
Visual Dashboard Analysis
Captures and analyzes the visual elements of the dashboard
"""

import requests
import re
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"
DASHBOARD_URL = urljoin(BASE_URL, "/dashboard/")

def analyze_dashboard_html():
    """Get and analyze the actual dashboard HTML"""
    try:
        response = requests.get(DASHBOARD_URL)
        if response.status_code == 200:
            html = response.text
            
            print("🎨 DASHBOARD HTML ANALYSIS")
            print("="*50)
            
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                print(f"📄 Page Title: {title_match.group(1).strip()}")
            
            # Look for main content areas
            print(f"\n📋 Content Structure:")
            
            # Count key elements
            counts = {
                'divs': len(re.findall(r'<div', html, re.IGNORECASE)),
                'sections': len(re.findall(r'<section', html, re.IGNORECASE)),
                'cards': len(re.findall(r'class="[^"]*card[^"]*"', html, re.IGNORECASE)),
                'charts': len(re.findall(r'chart|graph', html, re.IGNORECASE)),
                'tables': len(re.findall(r'<table', html, re.IGNORECASE)),
                'buttons': len(re.findall(r'<button', html, re.IGNORECASE)),
                'forms': len(re.findall(r'<form', html, re.IGNORECASE)),
            }
            
            for element, count in counts.items():
                print(f"  • {element.capitalize()}: {count}")
            
            # Look for specific dashboard content
            print(f"\n📊 Dashboard Elements:")
            
            # Search for numbers/metrics that might be KPIs
            numbers = re.findall(r'\b\d{1,6}\b', html)
            if numbers:
                print(f"  • Potential KPI values found: {len(set(numbers))} unique numbers")
                # Show some examples
                unique_numbers = list(set(numbers))[:10]
                print(f"    Examples: {', '.join(unique_numbers)}")
            
            # Look for dashboard-specific classes or IDs
            dashboard_elements = re.findall(r'class="[^"]*(?:dashboard|chart|metric|kpi|stat)[^"]*"', html, re.IGNORECASE)
            if dashboard_elements:
                print(f"  • Dashboard CSS classes found: {len(dashboard_elements)}")
                for elem in dashboard_elements[:5]:  # Show first 5
                    print(f"    - {elem}")
            
            # Look for navigation or menu items
            nav_items = re.findall(r'<(?:nav|ul|li)[^>]*>.*?</(?:nav|ul|li)>', html, re.IGNORECASE | re.DOTALL)
            if nav_items:
                print(f"  • Navigation elements: {len(nav_items)}")
            
            # Check for Bootstrap or other frameworks
            print(f"\n🎨 UI Framework Detection:")
            frameworks = {
                'Bootstrap': 'bootstrap' in html.lower(),
                'Tailwind': 'tailwind' in html.lower(),
                'Bulma': 'bulma' in html.lower(),
                'Foundation': 'foundation' in html.lower(),
                'Material UI': 'material' in html.lower(),
            }
            
            for framework, found in frameworks.items():
                status = "✅ Detected" if found else "❌ Not found"
                print(f"  • {framework}: {status}")
            
            # Extract and display actual visible text content
            print(f"\n📝 Main Content Text:")
            
            # Remove scripts and styles
            clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            
            # Extract text content
            text_content = re.sub(r'<[^>]+>', ' ', clean_html)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Get meaningful words (longer than 3 characters)
            words = [word for word in text_content.split() if len(word) > 3]
            
            if words:
                print(f"  • Total words: {len(words)}")
                print(f"  • First 50 words: {' '.join(words[:50])}")
            
            print(f"\n📄 RAW HTML SAMPLE (first 1000 chars):")
            print("-" * 50)
            print(html[:1000])
            if len(html) > 1000:
                print(f"\n... (truncated, total length: {len(html)} characters)")
            
            return html
            
        else:
            print(f"❌ Failed to access dashboard: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing dashboard: {e}")
        return None

if __name__ == "__main__":
    analyze_dashboard_html()
