"""
HotpotQA Preprocessing and Normalization Script for EvidenRoute.

Reads the official HotpotQA development set (hotpot_dev_distractor_v1.json),
extracts multi-hop questions, supporting facts, and distractor paragraphs,
and normalizes them into EvidenRoute's evidence format without modifying the raw dataset.

Output files:
- data/processed/hotpotqa_evidence.jsonl (Normalized evidence chunks)
- data/benchmarks/hotpotqa_sample_benchmarks.jsonl (Evaluation benchmark questions)
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

RAW_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "hotpot_dev_distractor_v1.json")
PROCESSED_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "hotpotqa_evidence.jsonl")
BENCHMARK_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "benchmarks", "hotpotqa_sample_benchmarks.jsonl")


def prepare_hotpotqa(
    raw_path: str = RAW_FILE,
    output_evidence_path: str = PROCESSED_FILE,
    output_benchmark_path: str = BENCHMARK_FILE,
    sample_limit: int = 100,
) -> bool:
    print("=" * 70)
    print("  EVIDENROUTE - HOTPOTQA PREPROCESSING PIPELINE")
    print("=" * 70)
    print(f"Raw Input File    : {raw_path}")
    print(f"Output Evidence   : {output_evidence_path}")
    print(f"Output Benchmarks : {output_benchmark_path}")
    print(f"Sample Limit      : {sample_limit} QA examples")

    if not os.path.exists(raw_path):
        print(f"\n[ERROR] Raw HotpotQA dataset not found at: {raw_path}")
        print("\nPlease run the download script first:")
        print("  python scripts/download_hotpotqa.py")
        print("\nOr download manually from:")
        print("  https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json")
        print(f"and place it at: {raw_path}")
        return False

    os.makedirs(os.path.dirname(output_evidence_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_benchmark_path), exist_ok=True)

    print("\nReading raw JSON dataset...")
    try:
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}", file=sys.stderr)
        return False

    total_records = len(raw_data)
    print(f"Total examples in raw dataset: {total_records:,}")

    subset = raw_data[:sample_limit]
    evidence_count = 0
    benchmark_count = 0
    seen_evidence_ids = set()

    with open(output_evidence_path, "w", encoding="utf-8") as ev_out, \
         open(output_benchmark_path, "w", encoding="utf-8") as bm_out:

        for idx, item in enumerate(subset):
            qa_id = item.get("_id", f"hp_{idx}")
            question = item.get("question", "").strip()
            answer = item.get("answer", "").strip()
            supporting_facts = item.get("supporting_facts", [])  # list of [title, sentence_idx]
            supporting_titles = {sf[0] for sf in supporting_facts if len(sf) > 0}
            context = item.get("context", [])  # list of [title, [sentence1, sentence2...]]

            expected_evidence_ids = []

            for ctx_idx, ctx_entry in enumerate(context):
                if len(ctx_entry) < 2:
                    continue
                title = ctx_entry[0]
                sentences = ctx_entry[1]
                content = " ".join(sentences).strip()
                if not content:
                    continue

                evidence_id = f"hotpot_{qa_id}_{ctx_idx}"
                is_supporting = title in supporting_titles
                if is_supporting:
                    expected_evidence_ids.append(evidence_id)

                # Avoid duplicate evidence chunks across questions
                if evidence_id not in seen_evidence_ids:
                    seen_evidence_ids.add(evidence_id)
                    evidence_record = {
                        "record_id": evidence_id,
                        "source_id": "hotpotqa_wikipedia",
                        "source_type": "document",
                        "title": f"Wikipedia: {title}",
                        "content": content,
                        "uri": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                        "author": "HotpotQA / English Wikipedia",
                        "authority_score": 0.85,
                        "created_at": "2018-09-01T00:00:00Z",
                        "updated_at": "2018-09-01T00:00:00Z",
                        "metadata": {
                            "hotpot_id": qa_id,
                            "dataset": "hotpot_dev_distractor_v1",
                            "is_supporting_fact": is_supporting,
                            "sentence_count": len(sentences),
                            "synthetic": False,
                        },
                    }
                    ev_out.write(json.dumps(evidence_record) + "\n")
                    evidence_count += 1

            benchmark_entry = {
                "benchmark_id": f"bm_hotpot_{qa_id}",
                "question": question,
                "expected_answer": answer,
                "expected_evidence_ids": expected_evidence_ids,
                "expected_source_types": ["document"],
                "expected_decision": "ANSWER",
                "test_category": "multi_hop_retrieval",
                "metadata": {
                    "dataset": "HotpotQA",
                    "level": item.get("level", "medium"),
                    "type": item.get("type", "comparison"),
                },
            }
            bm_out.write(json.dumps(benchmark_entry) + "\n")
            benchmark_count += 1

    print("\n[SUCCESS] HotpotQA Preprocessing completed!")
    print(f"  * Normalized Evidence Records saved: {evidence_count:,} -> {output_evidence_path}")
    print(f"  * Benchmark QA Questions saved     : {benchmark_count:,} -> {output_benchmark_path}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess HotpotQA dataset for EvidenRoute")
    parser.add_argument("--limit", type=int, default=100, help="Number of QA examples to process (default: 100)")
    parser.add_argument("--raw", type=str, default=RAW_FILE, help="Path to raw JSON file")
    args = parser.parse_args()

    success = prepare_hotpotqa(raw_path=args.raw, sample_limit=args.limit)
    sys.exit(0 if success else 1)
