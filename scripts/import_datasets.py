"""
Optional Dataset Importer for EvidenRoute.

This script allows developers to explicitly import local synthetic datasets into
the EvidenRoute database using the existing source ingestion API interface.

SAFETY RULES:
- Never executed automatically.
- Requires explicit user confirmation or '--confirm' flag.
- Supports dry-run mode ('--dry-run') to preview operations without database writes.
- Uses existing backend contracts exclusively without modifying any schemas.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKETS_FILE = os.path.join(BASE_DIR, "data", "synthetic", "sample_tickets.jsonl")
CONVERSATIONS_FILE = os.path.join(BASE_DIR, "data", "synthetic", "sample_conversations.jsonl")


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    records = []
    if not os.path.exists(file_path):
        print(f"[WARN] File not found: {file_path}")
        return records
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))
    return records


def import_records_via_api(api_base_url: str, source_id: str, records: List[Dict[str, Any]], dry_run: bool = False) -> bool:
    import httpx

    print(f"\nProcessing {len(records)} records for source: '{source_id}'...")
    if dry_run:
        print(f"  [DRY RUN] Would submit batch of {len(records)} records to {api_base_url}/api/sources/ingest")
        return True

    payload = {
        "source_id": source_id,
        "records": records,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{api_base_url}/api/sources/ingest", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                print(f"  [SUCCESS] Ingested {data.get('ingested_in_batch')} records. Total in source: {data.get('total_source_records')}")
                return True
            else:
                print(f"  [ERROR] Ingestion failed (HTTP {resp.status_code}): {resp.text}")
                return False
    except Exception as e:
        print(f"  [ERROR] Could not connect to API server at {api_base_url}: {e}")
        print("  Hint: Ensure the backend is running with 'python -m uvicorn backend.app.main:app'")
        return False


def main():
    parser = argparse.ArgumentParser(description="EvidenRoute Safe Dataset Importer")
    parser.add_argument("--confirm", action="store_true", help="Confirm execution without interactive prompt")
    parser.add_argument("--dry-run", action="store_true", help="Preview import without writing to database")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="EvidenRoute API base URL")
    args = parser.parse_args()

    print("=" * 75)
    print("        EVIDENROUTE OPTIONAL DATASET IMPORTER (SAFE UTILITY)")
    print("=" * 75)

    tickets = load_jsonl(TICKETS_FILE)
    conversations = load_jsonl(CONVERSATIONS_FILE)

    print(f"Loaded {len(tickets)} synthetic tickets from: {TICKETS_FILE}")
    print(f"Loaded {len(conversations)} synthetic conversations from: {CONVERSATIONS_FILE}")

    if not args.confirm and not args.dry_run:
        print("\nWARNING: This will import records into your local EvidenRoute database.")
        choice = input("Do you wish to proceed? [y/N]: ").strip().lower()
        if choice not in ("y", "yes"):
            print("Import cancelled by user.")
            sys.exit(0)

    # 1. Ingest tickets into 'support_tickets' source
    success_tickets = import_records_via_api(
        api_base_url=args.api_url,
        source_id="support_tickets",
        records=tickets,
        dry_run=args.dry_run,
    )

    # 2. Ingest conversations into 'slack_conversations' source
    success_convs = import_records_via_api(
        api_base_url=args.api_url,
        source_id="slack_conversations",
        records=conversations,
        dry_run=args.dry_run,
    )

    if success_tickets and success_convs:
        print("\n[COMPLETE] All selected dataset records processed successfully.")
    else:
        print("\n[PARTIAL/FAILED] One or more batch imports encountered an issue.")


if __name__ == "__main__":
    main()
