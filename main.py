"""
Document Forensic Analysis - CLI Entry Point

Usage:
    python main.py <path_to_image_or_pdf>
    python main.py forensic_test_dataset/splicing/01_splicing.jpg
"""

import sys
import os
from forensics.analyzer import analyze_forensics


def format_report(result):
    """Format a forensic analysis result into a clean, human-readable report."""
    if not result.get("success", False):
        print("\n" + "=" * 50)
        print("       DOCUMENT FORENSIC ANALYSIS (FAILED)")
        print("=" * 50)
        print(f"Error: {result.get('message', 'Unknown error')}")
        if "file" in result:
            print(f"File : {result['file']}")
        print("=" * 50 + "\n")
        return

    file_path = result.get("file", "Unknown")
    filename = os.path.basename(file_path)
    score = result.get("document_forensic_score", 0)
    risk = result.get("document_risk_level", "LOW")

    pages = result.get("results", [])
    confidence = 1.0
    active_signals = []
    evidence = []
    outputs = []

    if pages:
        p0 = pages[0]
        fs = p0.get("forensic_score", {})
        confidence = fs.get("confidence", 1.0)
        active_signals = fs.get("active_signals", [])
        evidence = fs.get("evidence", [])

        # Collect visualization outputs
        for mod in ["ela", "edge_analysis", "jpeg_analysis", "noise", "copy_move", "resampling"]:
            if mod in p0 and isinstance(p0[mod], dict) and "output" in p0[mod]:
                outputs.append(p0[mod]["output"])

    print("\n" + "=" * 50)
    print("       DOCUMENT FORENSIC ANALYSIS")
    print("=" * 50)
    print(f"\nImage: {filename}")
    print(f"\nFORENSIC SCORE : {score}/100")
    print(f"RISK LEVEL     : {risk}")
    print(f"CONFIDENCE     : {confidence:.2f}")

    print("\nACTIVE SIGNALS:")
    if active_signals:
        for sig in active_signals:
            print(f"  - {sig}")
    else:
        print("  - None (No significant anomalies detected)")

    print("\nEVIDENCE:")
    if evidence:
        for item in evidence:
            print(f"  - {item}")
    else:
        print("  - No tampering evidence detected")

    if outputs:
        print("\nOUTPUTS:")
        for out in outputs[:5]:
            print(f"  {out}")

    print("\n" + "=" * 50 + "\n")


def main():
    if len(sys.argv) < 2:
        default_file = os.path.join("forensic_test_dataset", "splicing", "01_splicing.jpg")
        if os.path.exists(default_file):
            print(f"No file path provided. Running analysis on default sample: {default_file}")
            file_path = default_file
        else:
            print("Usage: python main.py <path_to_image_or_pdf>")
            sys.exit(1)
    else:
        file_path = sys.argv[1].strip('"').strip("'")

    if not os.path.exists(file_path):
        print(f"Error: File not found: '{file_path}'")
        sys.exit(1)

    result = analyze_forensics(file_path)
    format_report(result)


if __name__ == "__main__":
    main()
