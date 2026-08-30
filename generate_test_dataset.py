import os
import cv2
import shutil
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = "pantest"
OUTPUT_DIR = "forensic_test_dataset"

# Number of images to process
MAX_IMAGES = 20

# Reproducible transformations
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Visible marker added to generated test images
WATERMARK = "SYNTHETIC TEST - NOT VALID"

# ============================================================
# DIRECTORY SETUP
# ============================================================

CLASSES = [
    "original",
    "text_addition",
    "text_replacement",
    "covering_patch",
    "photo_replacement",
    "copy_move",
    "removal",
    "splicing",
    "resampling",
    "jpeg_recompression",
    "noise",
    "combined",
]

for cls in CLASSES:
    os.makedirs(
        os.path.join(OUTPUT_DIR, cls),
        exist_ok=True
    )


# ============================================================
# IMAGE UTILITIES
# ============================================================

def load_image(path):
    img = cv2.imread(path)

    if img is None:
        raise ValueError(f"Could not read image: {path}")

    return img


def save_image(path, img, quality=95):
    ext = os.path.splitext(path)[1].lower()

    if ext in [".jpg", ".jpeg"]:
        cv2.imwrite(
            path,
            img,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
    else:
        cv2.imwrite(path, img)


def resize_for_processing(img, max_width=1600):
    h, w = img.shape[:2]

    if w <= max_width:
        return img

    scale = max_width / w

    return cv2.resize(
        img,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_AREA
    )


# ============================================================
# SYNTHETIC MARKER
# ============================================================

def add_synthetic_marker(img):
    """
    Adds a visible marker to ensure generated data is clearly
    synthetic/test-only.

    The marker is deliberately placed in a corner rather than
    modifying identity fields.
    """

    result = img.copy()

    h, w = result.shape[:2]

    font_scale = max(0.45, min(w, h) / 1000)

    thickness = max(1, int(font_scale * 2))

    # Bottom-left placement
    x = 10
    y = h - 15

    cv2.putText(
        result,
        WATERMARK,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 0, 255),
        thickness,
        cv2.LINE_AA
    )

    return result


# ============================================================
# SAFE TEST REGION
# ============================================================

def get_test_region(img):
    """
    Returns a region used for synthetic forensic transformations.

    We intentionally use the central/background area instead of
    attempting to modify PAN numbers, names, DOB, signatures,
    photographs, or QR/security regions.
    """

    h, w = img.shape[:2]

    # Central background area
    x1 = int(w * 0.35)
    x2 = int(w * 0.65)

    y1 = int(h * 0.35)
    y2 = int(h * 0.65)

    return x1, y1, x2, y2


# ============================================================
# 1. TEXT ADDITION
# ============================================================

def text_addition(img):
    """
    Adds clearly synthetic text to a background area.

    Detector:
        text_tampering / ELA / edge analysis
    """

    result = img.copy()

    h, w = result.shape[:2]

    text = "TEST EDIT"

    x = int(w * 0.42)
    y = int(h * 0.50)

    cv2.putText(
        result,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (80, 80, 80),
        2,
        cv2.LINE_AA
    )

    return result


# ============================================================
# 2. TEXT REPLACEMENT
# ============================================================

def text_replacement(img):
    """
    Replaces synthetic test text in a dedicated background area.

    We do NOT replace actual PAN/name/DOB information.
    """

    result = img.copy()

    h, w = result.shape[:2]

    x = int(w * 0.40)
    y = int(h * 0.50)

    # Background rectangle
    cv2.rectangle(
        result,
        (x - 10, y - 35),
        (x + 180, y + 10),
        (210, 210, 210),
        -1
    )

    cv2.putText(
        result,
        "ALTERED",
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (50, 50, 50),
        2,
        cv2.LINE_AA
    )

    return result


# ============================================================
# 3. COVERING PATCH
# ============================================================

def covering_patch(img):
    """
    Simulates a covering/obscuring operation on a background area.
    """

    result = img.copy()

    x1, y1, x2, y2 = get_test_region(img)

    # Smaller patch
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    pw = max(30, int(img.shape[1] * 0.08))
    ph = max(20, int(img.shape[0] * 0.08))

    cv2.rectangle(
        result,
        (cx - pw, cy - ph),
        (cx + pw, cy + ph),
        (245, 245, 245),
        -1
    )

    return result


# ============================================================
# 4. PHOTO-LIKE SPLICE
# ============================================================

def photo_replacement(img):
    """
    Inserts a synthetic colored texture block into a background
    region.

    This tests splice-boundary detection without creating a
    replacement identity photograph.
    """

    result = img.copy()

    h, w = img.shape[:2]

    x1 = int(w * 0.38)
    y1 = int(h * 0.30)

    width = int(w * 0.10)
    height = int(h * 0.15)

    patch = np.zeros(
        (height, width, 3),
        dtype=np.uint8
    )

    # Synthetic texture
    patch[:] = (
        random.randint(80, 180),
        random.randint(80, 180),
        random.randint(80, 180)
    )

    noise = np.random.normal(
        0,
        20,
        patch.shape
    ).astype(np.int16)

    patch = np.clip(
        patch.astype(np.int16) + noise,
        0,
        255
    ).astype(np.uint8)

    result[
        y1:y1 + height,
        x1:x1 + width
    ] = patch

    return result


# ============================================================
# 5. COPY-MOVE
# ============================================================

def copy_move(img):
    """
    Copies a small background texture region to another location.

    Detector:
        copy_move.py
    """

    result = img.copy()

    h, w = img.shape[:2]

    # Source region
    sx = int(w * 0.35)
    sy = int(h * 0.40)

    sw = max(20, int(w * 0.06))
    sh = max(20, int(h * 0.06))

    # Destination
    dx = int(w * 0.55)
    dy = int(h * 0.55)

    source = img[
        sy:sy + sh,
        sx:sx + sw
    ].copy()

    if source.size == 0:
        return result

    result[
        dy:dy + sh,
        dx:dx + sw
    ] = source

    return result


# ============================================================
# 6. REMOVAL / INPAINTING
# ============================================================

def removal(img):
    """
    Removes a synthetic background region using OpenCV
    inpainting.

    Detector:
        ELA
        noise
        edge analysis
    """

    result = img.copy()

    h, w = img.shape[:2]

    x = int(w * 0.44)
    y = int(h * 0.45)

    rw = max(30, int(w * 0.07))
    rh = max(20, int(h * 0.06))

    mask = np.zeros(
        (h, w),
        dtype=np.uint8
    )

    cv2.rectangle(
        mask,
        (x, y),
        (x + rw, y + rh),
        255,
        -1
    )

    result = cv2.inpaint(
        result,
        mask,
        5,
        cv2.INPAINT_TELEA
    )

    return result


# ============================================================
# 7. SPLICING
# ============================================================

def splicing(img):
    """
    Inserts a synthetic patch with different image statistics.
    """

    result = img.copy()

    h, w = img.shape[:2]

    x = int(w * 0.50)
    y = int(h * 0.30)

    pw = max(40, int(w * 0.10))
    ph = max(30, int(h * 0.10))

    patch = img[
        max(0, y - ph):y,
        max(0, x - pw):x
    ].copy()

    if patch.size == 0:
        return result

    # Alter statistics of patch
    patch = cv2.GaussianBlur(
        patch,
        (7, 7),
        0
    )

    patch = cv2.convertScaleAbs(
        patch,
        alpha=1.35,
        beta=15
    )

    ph2, pw2 = patch.shape[:2]

    result[
        y:y + ph2,
        x:x + pw2
    ] = patch

    return result


# ============================================================
# 8. RESAMPLING
# ============================================================

def resampling(img):
    """
    Downscale + upscale.

    Detector:
        resampling.py
        JPEG/ELA
    """

    h, w = img.shape[:2]

    small_w = max(100, int(w * 0.55))
    small_h = max(100, int(h * 0.55))

    down = cv2.resize(
        img,
        (small_w, small_h),
        interpolation=cv2.INTER_AREA
    )

    up = cv2.resize(
        down,
        (w, h),
        interpolation=cv2.INTER_CUBIC
    )

    return up


# ============================================================
# 9. JPEG RECOMPRESSION
# ============================================================

def jpeg_recompression(img):
    """
    JPEG recompression at lower quality.

    Detector:
        jpeg_analysis.py
        ELA
    """

    temp_path = os.path.join(
        OUTPUT_DIR,
        "_temporary_recompression.jpg"
    )

    cv2.imwrite(
        temp_path,
        img,
        [cv2.IMWRITE_JPEG_QUALITY, 55]
    )

    result = cv2.imread(temp_path)

    try:
        os.remove(temp_path)
    except OSError:
        pass

    return result


# ============================================================
# 10. NOISE INJECTION
# ============================================================

def noise_tampering(img):
    """
    Adds localized noise to a background area.

    Detector:
        noise.py
    """

    result = img.copy()

    h, w = img.shape[:2]

    x1 = int(w * 0.45)
    y1 = int(h * 0.40)

    rw = max(40, int(w * 0.10))
    rh = max(30, int(h * 0.10))

    region = result[
        y1:y1 + rh,
        x1:x1 + rw
    ].copy()

    if region.size == 0:
        return result

    noise = np.random.normal(
        0,
        25,
        region.shape
    )

    noisy = np.clip(
        region.astype(np.float32) + noise,
        0,
        255
    ).astype(np.uint8)

    result[
        y1:y1 + rh,
        x1:x1 + rw
    ] = noisy

    return result


# ============================================================
# 11. COMBINED TAMPERING
# ============================================================

def combined_tampering(img):
    """
    Applies multiple independent forensic transformations.

    This is important for testing your new risk_score.py.

    Signals:
        ELA
        noise
        copy-move
        resampling
        splice-like region
    """

    result = img.copy()

    # 1. Synthetic text
    result = text_addition(result)

    # 2. Covering patch
    result = covering_patch(result)

    # 3. Copy move
    result = copy_move(result)

    # 4. Local noise
    result = noise_tampering(result)

    # 5. Resampling
    result = resampling(result)

    return result


# ============================================================
# APPLY TRANSFORMATION
# ============================================================

TRANSFORMATIONS = {
    "text_addition": text_addition,
    "text_replacement": text_replacement,
    "covering_patch": covering_patch,
    "photo_replacement": photo_replacement,
    "copy_move": copy_move,
    "removal": removal,
    "splicing": splicing,
    "resampling": resampling,
    "jpeg_recompression": jpeg_recompression,
    "noise": noise_tampering,
    "combined": combined_tampering,
}


# ============================================================
# MAIN DATASET GENERATION
# ============================================================

def main():

    print("=" * 70)
    print("SYNTHETIC FORENSIC TEST DATASET GENERATOR")
    print("=" * 70)

    if not os.path.exists(INPUT_DIR):

        print(
            f"\nERROR: Input folder '{INPUT_DIR}' does not exist."
        )

        print(
            "\nCreate it and place your 20 images inside:"
        )

        print(
            f"    {INPUT_DIR}\\"
        )

        return

    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
    ]

    files.sort()

    if not files:

        print(
            f"\nERROR: No images found in {INPUT_DIR}"
        )

        return

    files = files[:MAX_IMAGES]

    print(
        f"\nFound {len(files)} input images."
    )

    # --------------------------------------------------------
    # ORIGINALS
    # --------------------------------------------------------

    print("\nCreating synthetic originals...")

    for index, filename in enumerate(files, start=1):

        source = os.path.join(
            INPUT_DIR,
            filename
        )

        img = load_image(source)

        img = resize_for_processing(img)

        # Add visible synthetic marker
        img = add_synthetic_marker(img)

        output_name = (
            f"{index:02d}_original.jpg"
        )

        output_path = os.path.join(
            OUTPUT_DIR,
            "original",
            output_name
        )

        save_image(
            output_path,
            img,
            quality=95
        )

    # --------------------------------------------------------
    # TAMPERED DATA
    # --------------------------------------------------------

    for class_name, transform in TRANSFORMATIONS.items():

        print(
            f"\nCreating: {class_name}"
        )

        for index, filename in enumerate(files, start=1):

            source = os.path.join(
                INPUT_DIR,
                filename
            )

            img = load_image(source)

            img = resize_for_processing(img)

            # First mark the image as synthetic
            img = add_synthetic_marker(img)

            # Apply transformation
            try:
                tampered = transform(img)

            except Exception as exc:

                print(
                    f"  ERROR on {filename}: {exc}"
                )

                continue

            output_name = (
                f"{index:02d}_{class_name}.jpg"
            )

            output_path = os.path.join(
                OUTPUT_DIR,
                class_name,
                output_name
            )

            save_image(
                output_path,
                tampered,
                quality=95
            )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATASET GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"\nDataset location:\n"
        f"    {OUTPUT_DIR}"
    )

    print("\nClasses:")

    for cls in CLASSES:
        print(
            f"    {cls}"
        )

    print("\nExpected structure:")

    print(
        """
forensic_test_dataset/
│
├── original/
│   ├── 01_original.jpg
│   ├── 02_original.jpg
│   └── ...
│
├── text_addition/
├── text_replacement/
├── covering_patch/
├── photo_replacement/
├── copy_move/
├── removal/
├── splicing/
├── resampling/
├── jpeg_recompression/
├── noise/
└── combined/
"""
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "These generated files are synthetic forensic test data."
    )

    print(
        "Do not use them as identity documents."
    )


if __name__ == "__main__":
    main()