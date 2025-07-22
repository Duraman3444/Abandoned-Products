#!/usr/bin/env python3
"""
Create placeholder screenshots for visual regression report
This script creates sample screenshots when servers are not available
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_screenshot(title, description, filename, is_modern=True):
    """Create a placeholder screenshot with title and description"""
    
    # Create 1440x900 image
    width, height = 1440, 900
    
    # Choose colors based on theme
    if is_modern:
        bg_color = '#0D1117'  # Dark background
        text_color = '#E6EDF3'  # Light text
        accent_color = '#14b8a6'  # Teal accent
        theme_name = "Modern SchoolDriver"
    else:
        bg_color = '#FFFFFF'  # Light background
        text_color = '#333333'  # Dark text
        accent_color = '#007cba'  # Blue accent
        theme_name = "Legacy SchoolDriver"
    
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a standard font, fallback to default
    try:
        title_font = ImageFont.truetype("Arial", 60)
        subtitle_font = ImageFont.truetype("Arial", 36)
        desc_font = ImageFont.truetype("Arial", 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
    
    # Draw title
    title_bbox = draw.textbbox((0, 0), theme_name, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 200), theme_name, fill=accent_color, font=title_font)
    
    # Draw page title
    page_bbox = draw.textbbox((0, 0), title, font=subtitle_font)
    page_width = page_bbox[2] - page_bbox[0]
    page_x = (width - page_width) // 2
    draw.text((page_x, 300), title, fill=text_color, font=subtitle_font)
    
    # Draw description
    desc_bbox = draw.textbbox((0, 0), description, font=desc_font)
    desc_width = desc_bbox[2] - desc_bbox[0]
    desc_x = (width - desc_width) // 2
    draw.text((desc_x, 400), description, fill=text_color, font=desc_font)
    
    # Draw placeholder indicator
    placeholder_text = "[PLACEHOLDER SCREENSHOT]"
    placeholder_bbox = draw.textbbox((0, 0), placeholder_text, font=desc_font)
    placeholder_width = placeholder_bbox[2] - placeholder_bbox[0]
    placeholder_x = (width - placeholder_width) // 2
    draw.text((placeholder_x, 500), placeholder_text, fill=accent_color, font=desc_font)
    
    # Draw resolution info
    resolution_text = f"Resolution: {width}x{height}"
    resolution_bbox = draw.textbbox((0, 0), resolution_text, font=desc_font)
    resolution_width = resolution_bbox[2] - resolution_bbox[0]
    resolution_x = (width - resolution_width) // 2
    draw.text((resolution_x, 700), resolution_text, fill=text_color, font=desc_font)
    
    # Add border for modern theme
    if is_modern:
        draw.rectangle([10, 10, width-10, height-10], outline=accent_color, width=3)
    
    # Save image
    os.makedirs('docs/screenshots', exist_ok=True)
    img.save(f'docs/screenshots/{filename}')
    print(f"✅ Created placeholder: {filename}")

def main():
    """Create all placeholder screenshots"""
    
    print("🖼️ Creating placeholder screenshots for visual regression report...")
    
    # Define screenshots to create
    screenshots = [
        ("Login Page", "User authentication interface", "login"),
        ("Student Dashboard", "Main student portal overview", "dashboard"),
        ("Grades Page", "Academic performance tracking", "grades"),
        ("Assignments Page", "Assignment tracking and submission", "assignments"),
        ("Attendance Page", "Attendance records and analytics", "attendance"),
        ("Admin Interface", "Administrative management panel", "admin"),
    ]
    
    # Create both legacy and modern versions
    for title, description, page_id in screenshots:
        # Legacy version
        create_placeholder_screenshot(
            title, description, f"legacy_{page_id}.png", is_modern=False
        )
        
        # Modern version
        create_placeholder_screenshot(
            title, description, f"modern_{page_id}.png", is_modern=True
        )
    
    print("🎉 All placeholder screenshots created!")
    print("📁 Screenshots saved in: docs/screenshots/")
    print("📄 Update the visual regression report with actual screenshots when servers are available")

if __name__ == "__main__":
    main()
