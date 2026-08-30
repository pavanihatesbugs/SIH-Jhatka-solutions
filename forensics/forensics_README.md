# Forensics Module

A document and image forensic-analysis module for detecting potential signs of image manipulation and assessing document risk.

The module accepts **JPG, JPEG, PNG, and PDF** inputs. PDFs are converted page-by-page into PNG images before analysis. Each page is evaluated using multiple forensic techniques, and the results are combined into a page-level forensic score and an overall document-level risk assessment.

## Features

The module currently performs:

1. **Image Quality Analysis**
   - Image dimensions
   - Blur score using Laplacian variance
   - Average brightness

2. **Error Level Analysis (ELA)**
   - Creates a JPEG-compressed copy of the image
   - Compares the original and compressed images
   - Produces an ELA visualization and average ELA score

3. **Metadata Analysis**
   - Extracts image format, dimensions, and EXIF metadata for JPG/JPEG/PNG
   - Includes PDF metadata analysis support in `metadata.py`

4. **Noise Analysis**
   - Estimates the noise residual using Gaussian smoothing
   - Produces a noise visualization
   - Calculates an average noise score

5. **Copy-Move Detection**
   - Uses ORB keypoints and descriptors
   - Matches image features
   - Identifies spatially separated strong matches as possible copy-move evidence
   - Produces a visualization of suspicious points

6. **Forensic Risk Scoring**
   - Combines ELA, noise, copy-move, metadata, and image-quality signals
   - Produces a score from `0` to `100`
   - Produces `LOW`, `MEDIUM`, or `HIGH` risk
   - Provides evidence explaining the score

## Folder Structure

```text
forensics/
├── __init__.py
├── analyzer.py
├── copy_move.py
├── ela.py
├── input_handler.py
├── metadata.py
├── noise.py
├── quality.py
└── risk_score.py
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `analyzer.py` | Main pipeline that coordinates all forensic checks |
| `input_handler.py` | Loads images and converts PDF pages to PNG |
| `quality.py` | Calculates image dimensions, blur, and brightness |
| `ela.py` | Performs Error Level Analysis |
| `metadata.py` | Extracts image EXIF and PDF metadata |
| `noise.py` | Calculates and visualizes image noise |
| `copy_move.py` | Detects possible copy-move manipulation using ORB |
| `risk_score.py` | Calculates forensic score, risk level, confidence, and evidence |
| `__init__.py` | Makes the directory a Python package |

## Pipeline

```text
                    Input Document
                         │
              ┌──────────┴──────────┐
              │                     │
            Image                  PDF
         JPG/JPEG/PNG                │
              │              Convert pages to PNG
              │                     │
              └──────────┬──────────┘
                         │
                    Page Images
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Quality          ELA          Metadata
          │              │              │
          ├──────────────┼──────────────┤
          │              │              │
        Noise       Copy-Move       Raw Results
          │              │              │
          └──────────────┼──────────────┘
                         │
                  Forensic Scoring
                         │
              ┌──────────┴──────────┐
              │                     │
        Forensic Score          Evidence
            0–100                   │
              │                     │
        Risk Level             Explanation
       LOW/MEDIUM/HIGH
```

## Main Entry Point

The complete pipeline is exposed through:

```python
from forensics.analyzer import analyze_forensics

result = analyze_forensics("document.pdf")
```

The analyzer first validates the input, supports PDF/JPG/JPEG/PNG files, analyzes every resulting page, calculates a page-level forensic score, and then calculates a document-level score. For multi-page documents, the highest page score is used as the document score so that a suspicious page is not hidden by averaging it with other pages.

## Example

```python
from forensics.analyzer import analyze_forensics

result = analyze_forensics("test.pdf")

print("Success:", result["success"])
print("File:", result["file"])
print("Pages analyzed:", result["pages_analyzed"])
print("Document score:", result["document_forensic_score"])
print("Risk level:", result["document_risk_level"])

print("\nEvidence:")
for item in result["evidence"]:
    print("-", item)

for page in result["results"]:
    print("\nImage:", page["image"])
    print("Page score:", page["forensic_score"]["forensic_score"])
    print("Page risk:", page["forensic_score"]["risk_level"])
```

## Result Structure

A successful document-level result has the following general structure:

```python
{
    "success": True,
    "file": "...",
    "pages_analyzed": 1,
    "document_forensic_score": 0,
    "document_risk_level": "LOW",
    "evidence": [...],
    "results": [
        {
            "image": "...",
            "quality": {...},
            "ela": {...},
            "metadata": {...},
            "noise": {...},
            "copy_move": {...},
            "forensic_score": {
                "forensic_score": 0,
                "risk_level": "LOW",
                "confidence": 1.0,
                "evidence": [...]
            }
        }
    ]
}
```

## Risk Scoring

The forensic score is limited to the range **0–100**.

### ELA

- ELA score `> 10` → `+25`
- ELA score `> 5` → `+15`

### Noise

- Noise score `> 10` → `+20`
- Noise score `> 5` → `+10`

### Copy-Move

- Suspicious copy-move detection → `+30`

### Image Quality / Confidence

Poor image quality does not directly add fraud points. Instead, it reduces confidence:

- Blur score `< 100` → confidence `-0.20`
- Brightness `< 30` or `> 230` → confidence `-0.10`

Missing metadata is recorded as evidence but is **not automatically treated as fraud**.

### Risk Levels

| Score | Risk Level |
|---:|---|
| `< 30` | LOW |
| `30–59` | MEDIUM |
| `60–100` | HIGH |

The score is a heuristic forensic indicator. A high score indicates that the implemented checks found suspicious signals; it should not by itself be treated as definitive proof of document fraud.

## Dependencies

The current implementation imports the following external Python packages:

```text
opencv-python
numpy
Pillow
PyMuPDF
```

Install them with:

```bash
pip install opencv-python numpy Pillow PyMuPDF
```

## Output Files

Some analysis modules generate visualization files:

```text
ela_<image-name>
noise_<image-name>
copy_move_<image-name>
```

PDF pages are temporarily converted into:

```text
working/
└── page_1.png
└── page_2.png
...
```

The exact output location depends on the paths supplied to the individual analysis functions.

## Notes

- Supported main input formats: `.jpg`, `.jpeg`, `.png`, `.pdf`
- Metadata analysis for images currently supports JPG/JPEG/PNG.
- PDF input is converted to page images before the main forensic image-analysis pipeline runs.
- Individual forensic checks return structured dictionaries containing success/error information.
- The final result includes both raw forensic outputs and the calculated risk assessment.
