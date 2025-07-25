#!/usr/bin/env python3
"""
Generate placeholder app icons for SchoolDriver PWA
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_app_icon(size, output_path):
    """Create a simple app icon with the given size"""
    # Create a new image with blue background
    img = Image.new('RGB', (size, size), color='#007bff')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default
    try:
        font_size = max(16, size // 8)
        font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', font_size)
    except:
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size // 8)
        except:
            font = ImageFont.load_default()
    
    # Draw "SD" text (SchoolDriver)
    text = "SD"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Add a border
    draw.rectangle([0, 0, size-1, size-1], outline='#0056b3', width=2)
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created icon: {output_path}")

def main():
    """Generate all required icon sizes"""
    icon_dir = 'static/img'
    os.makedirs(icon_dir, exist_ok=True)
    
    # Standard PWA icon sizes
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        output_path = os.path.join(icon_dir, f'icon-{size}x{size}.png')
        create_app_icon(size, output_path)
    
    # Create favicon
    create_app_icon(32, os.path.join(icon_dir, 'favicon-32x32.png'))
    create_app_icon(16, os.path.join(icon_dir, 'favicon-16x16.png'))
    
    print(f"\nGenerated {len(sizes) + 2} app icons in {icon_dir}/")

if __name__ == '__main__':
    main()
