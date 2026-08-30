# Document Image Forensics Module

A multi-signal computer vision and digital forensics module designed for detecting tampering, splicing, copy-move duplication, covering patches, text alterations, and compression inconsistencies in identity and document images.

> **Disclaimer**: This system provides forensic evidence/risk estimation and is not a definitive legal determination of fraud.

---

## 1. Overview

The forensic pipeline analyzes input document images or multi-page PDFs across multiple independent mathematical and visual signals, producing:
- **Forensic Risk Score** (0–100)
- **Risk Classification** (`LOW`, `MEDIUM`, `HIGH`)
- **Confidence Score** (0.0–1.0)
- **Signal Breakdown** (per-detector ratings)
- **Active Forensic Signals** (confirmed corroborating indicators)
- **Explainable Evidence** (human-readable justification strings)
- **Visual Artifacts** (maps generated in `working/` for auditor review)

---

## 2. Architecture & Pipeline

```text
                           Input Document (JPG / PNG / PDF)
                                          │
                         ┌────────────────┴────────────────┐
                         │                                 │
                   Direct Image                       PDF Document
                         │                                 │
                         │                      Convert pages to images
                         │                                 │
                         └────────────────┬────────────────┘
                                          │
                                Multi-Signal Analysis
                                          │
      ┌─────────────┬─────────────┬───────┴─────┬─────────────┬─────────────┐
      │             │             │             │             │             │
   Quality         ELA          Noise       Copy-Move     Resampling      Edge & JPEG
 (Laplacian)    (absdiff)     (Variance)      (ORB)         (FFT)        (DCT & Sobel)
      │             │             │             │             │             │
      └─────────────┴─────────────┼─────────────┴─────────────┴─────────────┘
                                  │
                       Evidence Fusion Engine
                      (Corroboration & Weights)
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
             Forensic Score                 Audit Trails
            (0-100, Risk Level)         (Evidence & Maps in working/)
```

---

## 3. Forensic Detectors

The suite comprises 8 specialized detection components:

| Detector | Method | Primary Anomaly Detected |
|---|---|---|
| **ELA** (`ela.py`) | JPEG recompression at quality 90 & gradient-compensated difference | Spliced patches, modified text, covering overlays |
| **Edge Analysis** (`edge_analysis.py`) | Canny edge & contour morphology with ID layout filtering | Pasted rectangular patches, covering blocks |
| **JPEG Analysis** (`jpeg_analysis.py`) | 8x8 block Discrete Cosine Transform (DCT) energy & local difference | Inconsistent compression grids, recompression anomalies |
| **Copy-Move** (`copy_move.py`) | ORB feature descriptor matching with RANSAC affine verification | Duplicated stamps, repeated text, copied textures |
| **Noise Analysis** (`noise.py`) | High-frequency residual variance on background patches | Localized noise injection, synthetic patch insertion |
| **Resampling** (`resampling.py`) | 2D Fast Fourier Transform (FFT) spectral peak concentration | Scaling, rotation, bicubic interpolation artifacts |
| **Metadata** (`metadata.py`) | EXIF extraction and PDF structure inspection | Editing software signatures, missing capture info |
| **Quality** (`quality.py`) | Laplacian variance blur detection and brightness measurement | Blur/lighting degradation affecting confidence |

---

## 4. How Detectors Work

### A. Error Level Analysis (ELA)
Recompresses the image at standard JPEG Quality 90 and measures the pixel-level absolute difference. High-frequency font glyph edges are gradient-compensated to avoid false alarms on normal printed text, while anomalous pasted patches display distinct localized compression discrepancies.

### B. Edge Analysis
Extracts internal contours and tests for rectangularity, 4-sided border edge concentration, and interior/exterior contrast. Standard ID layout features (such as ID photo frames, header text banners, and signature boxes) are recognized to suppress false positives on genuine credentials.

### C. JPEG Block Analysis
Partitions the image into 8x8 pixel blocks, performs DCT transformation, and computes AC energy. Evaluates local 4-neighbor relative differences to identify localized clusters of block-level inconsistencies while ignoring natural document texture.

### D. Copy-Move Detection
Extracts scale-invariant ORB keypoints and searches for spatially separated feature pairs sharing identical displacement vectors. Confirms geometric validity using RANSAC affine partial transform estimation to reject random text glyph repeats.

### E. Noise Variance Analysis
Extracts the high-pass noise residual via median filtering across flat document background patches. Flags localized noise variance step discontinuities caused by pasted foreign assets.

### F. Resampling & Spectral Analysis
Computes 2D FFT on the gradient map to detect periodic interpolation patterns from affine transformations. Evaluates high-frequency spectral peak concentration.

---

## 5. Evidence Fusion & Risk Scoring

Scoring follows conservative, corroborated fusion principles:
1. **Conservative Baselines**: An isolated weak artifact (e.g. edge alone, noise alone, or normal JPEG variation) is capped at **LOW** risk ($\le 22$) to prevent false alarms on genuine documents.
2. **Corroboration Bonus**: When 2, 3, or more independent signals corroborate on the same document, agreement bonuses elevate the risk to **MEDIUM** (30–59) or **HIGH** (60–100).
3. **Quality-Weighted Confidence**: Blurry or extreme lighting conditions reduce confidence (0.50–1.0) rather than raising the fraud score.

### Risk Classifications
- **`LOW` (0–29)**: Authentic document or isolated minor visual artifact.
- **`MEDIUM` (30–59)**: Moderate suspicious patterns or two corroborating signals.
- **`HIGH` (60–100)**: Multiple independent strong forensic anomalies or confirmed geometric duplication.

---

## 6. Installation

Use the provided project virtual environment (`.venv`):

```bash
# Create virtual environment (Python 3.12 recommended)
python -m venv .venv

# Activate environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

---

## 7. Running the Module

### A. Hackathon CLI Demo
Analyze any image or PDF directly from the command line:

```bash
python main.py forensic_test_dataset/splicing/01_splicing.jpg
```

**Example Terminal Output:**
```text
==================================================
       DOCUMENT FORENSIC ANALYSIS
==================================================

Image: 01_splicing.jpg

FORENSIC SCORE : 48/100
RISK LEVEL     : MEDIUM
CONFIDENCE     : 1.00

ACTIVE SIGNALS:
  - COPY_MOVE
  - EDGE

EVIDENCE:
  - Geometrically consistent copy-move feature duplication detected
  - Localized suspicious internal boundary anomaly detected
  - No useful EXIF metadata available (normal for scans/screenshots)

OUTPUTS:
  working\ela_01_splicing.jpg
  working\edges_01_splicing.jpg
  working\jpeg_01_splicing.png
  working\noise_01_splicing.jpg
  working\copy_move_01_splicing.jpg

==================================================
```

### B. Python API Integration
```python
from forensics.analyzer import analyze_forensics

result = analyze_forensics("path/to/document.jpg")

print(f"Score: {result['document_forensic_score']}/100")
print(f"Risk: {result['document_risk_level']}")
print(f"Active: {result['results'][0]['forensic_score']['active_signals']}")
```

---

## 8. Test Dataset Runner

Run automated evaluation over all test categories in `forensic_test_dataset/`:

```bash
python test_forensics.py
```

---

## 9. Output Visualizations

Visual artifacts are generated in `working/`:
- `working/ela_<filename>.jpg` – Error Level Analysis map
- `working/edges_<filename>.jpg` – Boundary detection overlay
- `working/jpeg_<filename>.png` – DCT block energy anomaly map
- `working/noise_<filename>.jpg` – Normalized noise residual map
- `working/copy_move_<filename>.jpg` – Keypoint match vectors

---

## 10. Limitations

1. High compression from repeated social media / messaging app transfers can degrade high-frequency signals.
2. Low-resolution images (< 300 DPI) reduce keypoint density for copy-move analysis.
3. EXIF metadata is frequently stripped during web upload; missing metadata is considered neutral, not fraudulent.
