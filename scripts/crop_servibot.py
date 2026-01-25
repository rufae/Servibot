#!/usr/bin/env python3
"""Simple script to crop the left portion of Servibot.png (the figure) and save an avatar.

Usage:
  python scripts/crop_servibot.py [--ratio 0.45] [--out frontend/public/servibot_avatar.png]

This script requires Pillow: pip install pillow
"""
import os
import sys
from PIL import Image

def main():
    src = os.path.join(os.path.dirname(__file__), '..', 'Servibot.png')
    src = os.path.abspath(src)
    out_default = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'servibot_avatar.png')
    out_default = os.path.abspath(out_default)

    ratio = 0.45
    out_path = out_default

    # Simple CLI parsing
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--ratio' and i+1 < len(args):
            try:
                ratio = float(args[i+1])
            except:
                pass
        if a == '--out' and i+1 < len(args):
            out_path = args[i+1]

    if not os.path.exists(src):
        print('Source image not found:', src)
        sys.exit(2)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with Image.open(src) as im:
        w, h = im.size
        crop_w = int(w * ratio)
        # Crop left area (assumes figure is on the left side of the original)
        box = (0, 0, crop_w, h)
        cropped = im.crop(box)
        # Optionally resize to square avatar
        size = (512, 512)
        cropped = cropped.resize(size, Image.LANCZOS)
        cropped.save(out_path)
        print('Saved avatar to', out_path)

if __name__ == '__main__':
    main()
