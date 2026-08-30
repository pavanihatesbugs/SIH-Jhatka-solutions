import os
import json
import sys

from forensics.analyzer import analyze_forensics


# ============================================================
# CONFIGURATION
# ============================================================



DATASET_FOLDER = sys.argv[1] if len(sys.argv) > 1 else "dataset/pan"
OUTPUT_FILE = "genuine_results.json"


# ============================================================
# SUPPORTED IMAGE FORMATS
# ============================================================

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png"
)


# ============================================================
# FIND IMAGES
# ============================================================

files = []

for filename in sorted(
    os.listdir(DATASET_FOLDER)
):

    if filename.lower().endswith(
        SUPPORTED_EXTENSIONS
    ):

        files.append(
            os.path.join(
                DATASET_FOLDER,
                filename
            )
        )


print()
print("=" * 70)
print("             FORENSIC DATASET TEST")
print("=" * 70)

print(
    f"Dataset folder : {DATASET_FOLDER}"
)

print(
    f"Images found   : {len(files)}"
)

print("=" * 70)


# ============================================================
# ANALYZE
# ============================================================

results = []

for index, file_path in enumerate(
    files,
    start=1
):

    print()
    print(
        f"[{index}/{len(files)}] "
        f"Analyzing: {os.path.basename(file_path)}"
    )

    try:

        result = analyze_forensics(
            file_path
        )

        # ----------------------------------------------------
        # Extract useful document-level information
        # ----------------------------------------------------

        summary = {

            "file":
                file_path,

            "success":
                result.get(
                    "success",
                    False
                ),

            "document_forensic_score":
                result.get(
                    "document_forensic_score",
                    0
                ),

            "document_risk_level":
                result.get(
                    "document_risk_level",
                    "UNKNOWN"
                ),

            "pages_analyzed":
                result.get(
                    "pages_analyzed",
                    0
                ),

            "pages": []
        }

        # ----------------------------------------------------
        # Page results
        # ----------------------------------------------------

        for page in result.get(
            "results",
            []
        ):

            forensic = page.get(
                "forensic_score",
                {}
            )

            summary["pages"].append({

                "image":
                    page.get(
                        "image"
                    ),

                "signal_breakdown":
                    forensic.get(
                        "signal_breakdown",
                        {}
                    ),

                "active_signals":
                    forensic.get(
                        "active_signals",
                        []
                    ),

                "forensic_score":
                    forensic.get(
                        "forensic_score",
                        0
                    ),

                "risk_level":
                    forensic.get(
                        "risk_level",
                        "UNKNOWN"
                    ),

                "confidence":
                    forensic.get(
                        "confidence",
                        0
                    )
            })

        results.append(
            summary
        )

        # ----------------------------------------------------
        # Terminal summary
        # ----------------------------------------------------

        print(
            "Score:",
            summary[
                "document_forensic_score"
            ]
        )

        print(
            "Risk:",
            summary[
                "document_risk_level"
            ]
        )

    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )

        results.append({

            "file":
                file_path,

            "success":
                False,

            "error":
                str(e)
        })


# ============================================================
# SAVE JSON
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=4
    )


# ============================================================
# SUMMARY
# ============================================================

successful = [

    r for r in results

    if r.get(
        "success",
        False
    )
]

scores = [

    r.get(
        "document_forensic_score",
        0
    )

    for r in successful
]


print()
print("=" * 70)
print("                 TEST COMPLETE")
print("=" * 70)

print(
    "Successful:",
    len(successful)
)

print(
    "Failed:",
    len(results) - len(successful)
)

if scores:

    print(
        "Minimum score:",
        min(scores)
    )

    print(
        "Maximum score:",
        max(scores)
    )

    print(
        "Average score:",
        round(
            sum(scores) / len(scores),
            2
        )
    )

print()
print(
    "Results saved to:",
    OUTPUT_FILE
)

print("=" * 70)