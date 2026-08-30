"""
Forensic Test Dataset Runner

Automatically discovers and evaluates forensic test images across all categories
and produces a compact human-readable report.

Usage:
    python test_forensics.py
    python test_forensics.py forensic_test_dataset
"""

import sys
import os
import glob
import time
from forensics.analyzer import analyze_forensics


def discover_images(base_dir):
    """Recursively find all image files grouped by category folder."""
    supported_exts = {".jpg", ".jpeg", ".png"}
    categories = {}

    if not os.path.exists(base_dir):
        return categories

    for root, _, files in os.walk(base_dir):
        category = os.path.basename(root)
        if category == os.path.basename(base_dir):
            continue

        img_files = [
            os.path.join(root, f) for f in sorted(files)
            if os.path.splitext(f)[1].lower() in supported_exts
        ]

        if img_files:
            categories[category] = img_files

    return categories


def run_tests(base_dir="forensic_test_dataset"):
    print("=" * 86)
    print("                      FORENSIC PIPELINE TEST SUITE")
    print("=" * 86)
    print(f"Target Directory: {os.path.abspath(base_dir)}")

    categories = discover_images(base_dir)
    total_images = sum(len(imgs) for imgs in categories.values())

    if total_images == 0:
        print("No test images found in target directory.")
        return

    print(f"Categories Found: {len(categories)} ({total_images} total images)")
    print("=" * 86)
    print(f"{'CATEGORY':<22} {'FILE':<30} {'SCORE':<8} {'RISK':<8} {'ACTIVE SIGNALS'}")
    print("-" * 86)

    start_time = time.time()
    results = []
    category_scores = {}

    for cat_name, file_list in sorted(categories.items()):
        cat_scores = []
        for file_path in file_list:
            filename = os.path.basename(file_path)
            try:
                res = analyze_forensics(file_path)
                score = res.get("document_forensic_score", 0)
                risk = res.get("document_risk_level", "LOW")

                pages = res.get("results", [])
                active = []
                if pages:
                    active = pages[0].get("forensic_score", {}).get("active_signals", [])

                active_str = str(active) if active else "[]"
                print(f"{cat_name:<22} {filename:<30} {score:>3}/100  {risk:<8} {active_str}")
                cat_scores.append(score)
                results.append({"file": file_path, "category": cat_name, "score": score, "risk": risk, "success": True})
            except Exception as e:
                print(f"{cat_name:<22} {filename:<30} {'ERR':>3}     {'ERROR':<8} {str(e)[:25]}")
                results.append({"file": file_path, "category": cat_name, "score": 0, "risk": "ERROR", "success": False})

        if cat_scores:
            category_scores[cat_name] = cat_scores

    elapsed = time.time() - start_time
    print("=" * 86)
    print("                            SUMMARY REPORT")
    print("=" * 86)
    print(f"Total Analyzed   : {len(results)} images in {elapsed:.2f}s ({elapsed / max(len(results), 1):.2f}s / image)")
    successful = [r for r in results if r["success"]]
    print(f"Successful Runs  : {len(successful)} / {len(results)}")

    print("\nCATEGORY BREAKDOWN (Average Forensic Score & Risk):")
    for cat, scores in sorted(category_scores.items()):
        avg_score = sum(scores) / len(scores)
        primary_risk = "HIGH" if avg_score >= 60 else ("MEDIUM" if avg_score >= 30 else "LOW")
        print(f"  - {cat:<24} : Avg Score {avg_score:>5.1f}/100 ({primary_risk}) across {len(scores)} images")

    print("\n" + "=" * 86)


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "forensic_test_dataset"
    target_dir = target_dir.strip('"').strip("'")
    run_tests(target_dir)


if __name__ == "__main__":
    main()
