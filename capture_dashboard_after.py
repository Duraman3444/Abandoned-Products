#!/usr/bin/env python3
"""
Capture dashboard screenshot for "after" state documentation.
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def capture_dashboard_after():
    """Capture screenshot of the dashboard after styling updates."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("Navigating to dashboard...")
            
            # Try to access dashboard directly first
            response = await page.goto('http://localhost:8000/dashboard/', wait_until='networkidle')
            
            # Check if we're redirected to login
            current_url = page.url
            if 'login' in current_url:
                print("Authentication required, attempting to login...")
                
                # Try to login with admin credentials
                await page.fill('input[name="username"]', 'admin')
                await page.fill('input[name="password"]', 'admin')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                
                # Navigate to dashboard again
                await page.goto('http://localhost:8000/dashboard/', wait_until='networkidle')
            
            # Wait for any dynamic content to load
            await asyncio.sleep(2)
            
            # Create directory if it doesn't exist
            os.makedirs('docs/screenshots', exist_ok=True)
            
            # Capture screenshot
            screenshot_path = 'docs/screenshots/dashboard_after_uniformity.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"✓ Dashboard screenshot saved: {screenshot_path}")
            
            # Test light mode toggle if visible
            try:
                light_mode_toggle = await page.query_selector('[data-theme-toggle]')
                if light_mode_toggle:
                    print("Testing light mode toggle...")
                    await light_mode_toggle.click()
                    await asyncio.sleep(1)
                    
                    # Capture light mode screenshot
                    light_screenshot_path = 'docs/screenshots/dashboard_after_light_mode.png'
                    await page.screenshot(path=light_screenshot_path, full_page=True)
                    print(f"✓ Light mode screenshot saved: {light_screenshot_path}")
                else:
                    print("No light mode toggle found")
            except Exception as e:
                print(f"Light mode toggle test failed: {e}")
            
            await browser.close()
            return screenshot_path
            
        except Exception as e:
            print(f"Error capturing dashboard: {e}")
            await browser.close()
            return None

if __name__ == "__main__":
    result = asyncio.run(capture_dashboard_after())
    if result:
        print(f"\nScreenshot successfully saved to: {result}")
    else:
        print("\nFailed to capture screenshot")
