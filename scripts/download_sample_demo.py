#!/usr/bin/env python3
"""
Download a sample CS2 demo for testing.
Uses a publicly available demo from various sources.
"""
import os
import requests
import bz2
from tqdm import tqdm

DEMOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'demos')

def download_with_progress(url: str, filepath: str) -> bool:
    """Download file with progress bar."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, stream=True, headers=headers, timeout=120)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(filepath, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(filepath)) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def decompress_bz2(bz2_path: str, output_path: str) -> bool:
    """Decompress bz2 file."""
    try:
        print(f"Decompressing {os.path.basename(bz2_path)}...")
        with bz2.open(bz2_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(1024 * 1024)
                    if not chunk:
                        break
                    f_out.write(chunk)
        os.remove(bz2_path)
        return True
    except Exception as e:
        print(f"Decompression error: {e}")
        return False

def main():
    os.makedirs(DEMOS_DIR, exist_ok=True)

    # Check for existing demos
    existing = [f for f in os.listdir(DEMOS_DIR) if f.endswith('.dem')]
    if existing:
        print(f"Demo already exists: {existing[0]}")
        return True

    print("=" * 60)
    print("CS2 Sample Demo Downloader")
    print("=" * 60)
    print()

    # Try multiple sources
    demo_sources = [
        # Add public demo URLs here when available
        # HLTV demos require authentication, so we need alternatives
    ]

    print("No automatic demo sources configured.")
    print()
    print("Please manually download a demo:")
    print()
    print("Option 1: HLTV (Recommended for pro matches)")
    print("  1. Go to https://www.hltv.org/matches")
    print("  2. Click on any completed match")
    print("  3. Scroll down and click 'GOTV Demo'")
    print("  4. Extract the .dem file and place it in:")
    print(f"     {os.path.abspath(DEMOS_DIR)}")
    print()
    print("Option 2: Your own CS2 matches")
    print("  1. Open CS2 -> Watch -> Your Matches")
    print("  2. Download any match")
    print("  3. Find the .dem file in your CS2 folder")
    print("  4. Copy it to the demos folder")
    print()
    print("Option 3: FACEIT matches")
    print("  1. Go to faceit.com -> your profile -> matches")
    print("  2. Click on a match and download the demo")
    print()

    return False

if __name__ == "__main__":
    main()
