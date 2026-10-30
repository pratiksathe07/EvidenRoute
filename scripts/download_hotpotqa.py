"""
Download script for the official HotpotQA development distractor dataset.
Official source: https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json
Target path: data/raw/hotpot_dev_distractor_v1.json
"""

import json
import os
import sys
import urllib.request

HOTPOT_URL = "https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
TARGET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
TARGET_FILE = os.path.join(TARGET_DIR, "hotpot_dev_distractor_v1.json")


def download_hotpotqa(url: str = HOTPOT_URL, target_path: str = TARGET_FILE) -> bool:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    print("=" * 70)
    print("  EVIDENROUTE - HOTPOTQA DATASET DOWNLOADER")
    print("=" * 70)
    print(f"Source URL : {url}")
    print(f"Destination: {target_path}")

    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        print(f"\n[INFO] File already exists ({os.path.getsize(target_path):,} bytes).")
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[SUCCESS] Verified valid JSON with {len(data):,} QA examples.")
            return True
        except Exception as e:
            print(f"[WARN] Existing file corrupted ({e}). Re-downloading...")

    print("\nInitiating HTTP download...")
    try:
        headers = {"User-Agent": "EvidenRoute-Benchmark-Downloader/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, "wb") as out:
            total_size = resp.getheader("Content-Length")
            if total_size:
                print(f"Total size: {int(total_size):,} bytes (~{int(total_size)//(1024*1024)} MB)")
            downloaded = 0
            block_size = 65536
            while True:
                buf = resp.read(block_size)
                if not buf:
                    break
                out.write(buf)
                downloaded += len(buf)
                if total_size:
                    percent = downloaded * 100 // int(total_size)
                    print(f"\rDownloading: {downloaded:,} bytes ({percent}%)", end="", flush=True)
                else:
                    print(f"\rDownloading: {downloaded:,} bytes...", end="", flush=True)

        print("\n\nDownload completed. Verifying JSON structure...")
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[SUCCESS] HotpotQA dataset successfully verified: {len(data):,} questions found.")
        return True

    except Exception as exc:
        print(f"\n[ERROR] Download failed: {exc}", file=sys.stderr)
        print("\nManual Download Instructions:")
        print("  If your current environment lacks outbound internet access, you can download")
        print("  the file on your host machine or via browser and place it at:")
        print(f"    {target_path}")
        print("\n  Direct URL: https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json")
        print("  Or run: curl -o data/raw/hotpot_dev_distractor_v1.json https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json")
        return False


if __name__ == "__main__":
    success = download_hotpotqa()
    sys.exit(0 if success else 1)
