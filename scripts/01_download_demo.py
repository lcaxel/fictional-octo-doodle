#!/usr/bin/env python3
"""
Script to download a test CS2 demo from HLTV.

For production, you'll need to scrape HLTV or use their unofficial API.
For now, we'll use a publicly available demo URL.
"""
import os
import requests
from tqdm import tqdm
import bz2

DEMOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'demos')

def download_file(url: str, filepath: str) -> bool:
    """Download a file with progress bar."""
    try:
        response = requests.get(url, stream=True, timeout=60)
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
        print(f"Error downloading: {e}")
        return False

def decompress_bz2(bz2_path: str, output_path: str) -> bool:
    """Decompress a .bz2 file."""
    try:
        print(f"Decompressing {os.path.basename(bz2_path)}...")
        with bz2.open(bz2_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                # Read in chunks for large files
                while True:
                    chunk = f_in.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f_out.write(chunk)
        return True
    except Exception as e:
        print(f"Error decompressing: {e}")
        return False

def main():
    os.makedirs(DEMOS_DIR, exist_ok=True)

    # Sample demo - you can replace this with any HLTV demo URL
    # This is a placeholder - HLTV demos usually require authentication

    print("=" * 60)
    print("CS2 Demo Downloader")
    print("=" * 60)
    print()
    print("To download demos from HLTV, you need to:")
    print("1. Go to https://www.hltv.org/matches")
    print("2. Find a match you want to analyze")
    print("3. Click on 'GOTV Demo' link")
    print("4. Copy the download URL")
    print()

    # Check if demo already exists
    demo_files = [f for f in os.listdir(DEMOS_DIR) if f.endswith('.dem')]
    if demo_files:
        print(f"Found existing demos: {demo_files}")
        return demo_files[0]

    print("No demos found in /demos folder.")
    print()
    print("Please manually download a demo from HLTV and place the .dem file")
    print(f"in the '{os.path.abspath(DEMOS_DIR)}' folder.")
    print()
    print("Example sources for CS2 demos:")
    print("- https://www.hltv.org/matches (official pro matches)")
    print("- Faceit/ESEA match history (your own matches)")
    print()

    return None

if __name__ == "__main__":
    main()
