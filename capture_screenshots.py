#!/usr/bin/env python3
"""
Screenshot capture and performance measurement script for SchoolDriver modern interface.
"""
import asyncio
import time
from playwright.async_api import async_playwright

async def capture_screenshots():
    """Capture screenshots of key pages and measure performance."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        urls_to_capture = [
            {
                'url': 'http://localhost:8000/accounts/login/',
                'filename': 'login_page.png',
                'description': 'Login page'
            },
            {
                'url': 'http://localhost:8000/dashboard/',
                'filename': 'dashboard_page.png',
                'description': 'Dashboard page'
            },
            {
                'url': 'http://localhost:8000/admin/',
                'filename': 'admin_index.png',
                'description': 'Admin index'
            }
        ]
        
        results = {
            'screenshots': [],
            'performance': {},
            'issues': []
        }
        
        for url_info in urls_to_capture:
            try:
                print(f"Capturing {url_info['description']} at {url_info['url']}")
                
                # Measure page load time
                start_time = time.time()
                response = await page.goto(url_info['url'], wait_until='networkidle')
                load_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Wait a bit for any dynamic content
                await asyncio.sleep(1)
                
                # Capture screenshot
                screenshot_path = f"docs/screenshots/after/{url_info['filename']}"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                results['screenshots'].append({
                    'url': url_info['url'],
                    'path': screenshot_path,
                    'description': url_info['description']
                })
                
                results['performance'][url_info['url']] = {
                    'load_time_ms': round(load_time, 2),
                    'status_code': response.status if response else 'No response'
                }
                
                print(f"✓ Screenshot saved: {screenshot_path}")
                print(f"✓ Load time: {load_time:.2f}ms")
                
            except Exception as e:
                error_msg = f"Error capturing {url_info['url']}: {str(e)}"
                print(f"✗ {error_msg}")
                results['issues'].append(error_msg)
        
        await browser.close()
        return results

async def main():
    """Main function to run the screenshot capture."""
    print("Starting screenshot capture and performance measurement...")
    print("=" * 60)
    
    results = await capture_screenshots()
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    print("\nScreenshots created:")
    for screenshot in results['screenshots']:
        print(f"  - {screenshot['path']} ({screenshot['description']})")
    
    print("\nPerformance metrics:")
    for url, metrics in results['performance'].items():
        print(f"  - {url}: {metrics['load_time_ms']}ms (status: {metrics['status_code']})")
    
    if results['issues']:
        print("\nIssues encountered:")
        for issue in results['issues']:
            print(f"  - {issue}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
