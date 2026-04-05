#!/usr/bin/env python3
"""
Remove solid backgrounds (white/gray) from images for transparency.

Usage:
    python remove_bg.py <directory>     # Process all images in directory
    python remove_bg.py <file1> <file2> # Process specific files
    python remove_bg.py --check <path>  # Check if images have transparency
"""

import os
import sys
from PIL import Image


def remove_solid_background(img, threshold=200, tolerance=60):
    """Remove white/gray backgrounds aggressively."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    img = img.copy()
    pixels = img.load()
    width, height = img.size
    changed = 0
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 5:
                brightness = (r + g + b) / 3
                is_light = brightness >= threshold
                is_white = r >= 200 and g >= 200 and b >= 200
                is_gray = (
                    abs(int(r) - int(g)) <= tolerance and
                    abs(int(g) - int(b)) <= tolerance and
                    abs(int(r) - int(b)) <= tolerance and
                    brightness >= 150
                )
                
                if is_light or is_white or is_gray:
                    pixels[x, y] = (r, g, b, 0)
                    changed += 1
    
    return img, changed


def check_transparency(filepath):
    """Check if image has transparent pixels."""
    img = Image.open(filepath)
    if img.mode != 'RGBA':
        return False
    extrema = img.getextrema()
    return extrema[3][0] > 0


def process_file(filepath):
    """Process a single image file."""
    if not os.path.exists(filepath):
        print(f"  Error: File not found: {filepath}")
        return 0
    
    try:
        img = Image.open(filepath)
        result, changed = remove_solid_background(img)
        
        if changed > 0:
            result.save(filepath)
            print(f"  Fixed: {os.path.basename(filepath)} ({changed} pixels)")
        else:
            print(f"  No change: {os.path.basename(filepath)}")
        
        return changed
    except Exception as e:
        print(f"  Error {os.path.basename(filepath)}: {e}")
        return 0


def process_directory(dirpath):
    """Process all images in a directory."""
    if not os.path.isdir(dirpath):
        print(f"Error: Not a directory: {dirpath}")
        return 0
    
    extensions = ('.png', '.jpg', '.jpeg', '.ico')
    total_changed = 0
    files_found = []
    
    for filename in os.listdir(dirpath):
        if filename.lower().endswith(extensions):
            filepath = os.path.join(dirpath, filename)
            files_found.append(filepath)
    
    if not files_found:
        print(f"No image files found in {dirpath}")
        return 0
    
    print(f"Processing {len(files_found)} images in {dirpath}:\n")
    
    for filepath in sorted(files_found):
        total_changed += process_file(filepath)
    
    return total_changed


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    args = sys.argv[1:]
    
    if args[0] == '--check':
        if len(args) < 2:
            print("Usage: python remove_bg.py --check <path>")
            sys.exit(1)
        path = args[1]
        if os.path.isdir(path):
            print(f"Checking images in {path}:\n")
            for filename in sorted(os.listdir(path)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.ico')):
                    filepath = os.path.join(path, filename)
                    has_trans = check_transparency(filepath)
                    status = "transparent" if has_trans else "NO TRANSPARENCY"
                    print(f"  {filename}: {status}")
        else:
            has_trans = check_transparency(path)
            status = "transparent" if has_trans else "NO TRANSPARENCY"
            print(f"{path}: {status}")
        return
    
    total = 0
    for arg in args:
        if os.path.isdir(arg):
            total += process_directory(arg)
        else:
            total += process_file(arg)
    
    if total > 0:
        print(f"\nTotal: {total} pixels removed")


if __name__ == '__main__':
    main()
