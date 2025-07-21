#!/usr/bin/env python3
"""
Capture dashboard "before" state screenshot.
"""
import asyncio
from playwright.async_api import async_playwright

async def capture_dashboard():
    """Capture dashboard screenshot."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("Navigating to dashboard...")
            response = await page.goto('http://localhost:8000/dashboard/', wait_until='networkidle')
            
            # Wait a bit for any dynamic content
            await asyncio.sleep(2)
            
            # Capture screenshot
            screenshot_path = "docs/screenshots/dashboard_before_uniformity.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"✓ Screenshot saved: {screenshot_path}")
            print(f"✓ Status code: {response.status if response else 'No response'}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(capture_dashboard())
    if result:
        print(f"\nScreenshot path: {result}")
