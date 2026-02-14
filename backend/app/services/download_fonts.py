"""
download_fonts.py
-----------------
Downloads the Noto Sans font files required by pdf_writer.py
and places them in the fonts/ directory next to this script.

Run once before your first translation:
    python download_fonts.py
"""

import urllib.request
import os
import sys

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# GitHub raw URLs for Noto Sans fonts (Apache 2.0 licensed)
FONTS = {
    "NotoSansGujarati-Regular.ttf": (
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/"
        "main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf"
    ),
    "NotoSansGujarati-Bold.ttf": (
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/"
        "main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Bold.ttf"
    ),
    "NotoSansDevanagari-Regular.ttf": (
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/"
        "main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"
    ),
    "NotoSansDevanagari-Bold.ttf": (
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/"
        "main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
    ),
    "NotoSans-Regular.ttf": (
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/"
        "main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
    ),
    "NotoSans-Bold.ttf": (
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/"
        "main/hinted/ttf/NotoSans/NotoSans-Bold.ttf"
    ),
}


def main():
    os.makedirs(FONTS_DIR, exist_ok=True)
    print(f"📂 Font directory: {FONTS_DIR}\n")

    for filename, url in FONTS.items():
        dest = os.path.join(FONTS_DIR, filename)

        if os.path.exists(dest):
            size_kb = os.path.getsize(dest) // 1024
            print(f"   ✅ {filename} already exists ({size_kb} KB) — skipping")
            continue

        print(f"   ⬇️  Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, dest)
            size_kb = os.path.getsize(dest) // 1024
            print(f"   ✅ {filename} downloaded ({size_kb} KB)")
        except Exception as e:
            print(f"   ❌ Failed to download {filename}: {e}")
            # Clean up partial download
            if os.path.exists(dest):
                os.remove(dest)
            sys.exit(1)

    print("\n🎉 All fonts ready. You can run your translation now.")


if __name__ == "__main__":
    main()