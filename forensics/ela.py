import os
import cv2
import numpy as np


# ================================================================
# BASIC HELPERS
# ================================================================

def _ensure_directory(path):
    directory = os.path.dirname(path)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )


def _iou(box1, box2):
    """
    Intersection over Union.

    Box:
        (x, y, width, height)
    """

    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xa = max(x1, x2)
    ya = max(y1, y2)

    xb = min(
        x1 + w1,
        x2 + w2
    )

    yb = min(
        y1 + h1,
        y2 + h2
    )

    intersection = (
        max(0, xb - xa) *
        max(0, yb - ya)
    )

    area1 = w1 * h1
    area2 = w2 * h2

    union = (
        area1 +
        area2 -
        intersection
    )

    if union <= 0:
        return 0.0

    return intersection / union


def _box_center(box):
    x, y, w, h = box

    return (
        x + w // 2,
        y + h // 2
    )


def _distance_between_boxes(box1, box2):
    """
    Approximate distance between two boxes.
    """

    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    c1 = _box_center(box1)
    c2 = _box_center(box2)

    return np.sqrt(
        (
            c1[0] - c2[0]
        ) ** 2
        +
        (
            c1[1] - c2[1]
        ) ** 2
    )


# ================================================================
# DOCUMENT AREA
# ================================================================

def _find_document_area(image):
    """
    Find the approximate physical document/card area.

    For a photographed ID card, the card usually occupies a large
    rectangular portion of the image.

    If detection fails, use almost the entire image.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    height, width = gray.shape

    # Blur camera noise.
    blurred = cv2.GaussianBlur(
        gray,
        (7, 7),
        0
    )

    edges = cv2.Canny(
        blurred,
        40,
        120
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (15, 15)
    )

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    image_area = width * height

    best_box = None
    best_score = 0

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        if area < image_area * 0.35:
            continue

        aspect = w / max(h, 1)

        # ID cards are normally wider than tall.
        if aspect < 1.15 or aspect > 2.8:
            continue

        rectangularity = (
            cv2.contourArea(contour)
            /
            max(area, 1)
        )

        score = (
            (area / image_area) * 60
            +
            rectangularity * 40
        )

        if score > best_score:

            best_score = score

            best_box = (
                x,
                y,
                w,
                h
            )

    if best_box is None:

        # Ignore a small camera border.
        margin_x = int(
            width * 0.03
        )

        margin_y = int(
            height * 0.03
        )

        return (
            margin_x,
            margin_y,
            width - 2 * margin_x,
            height - 2 * margin_y
        )

    return best_box


# ================================================================
# GLOBAL ELA
# ================================================================

def _global_ela(
    image,
    quality=90
):
    """
    Traditional ELA.
    """

    temp_file = os.path.join(
        "working",
        "_temporary_ela.jpg"
    )

    _ensure_directory(
        temp_file
    )

    success = cv2.imwrite(
        temp_file,
        image,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            quality
        ]
    )

    if not success:
        return None, None

    compressed = cv2.imread(
        temp_file
    )

    try:
        os.remove(
            temp_file
        )
    except Exception:
        pass

    if compressed is None:
        return None, None

    difference = cv2.absdiff(
        image,
        compressed
    )

    difference = cv2.cvtColor(
        difference,
        cv2.COLOR_BGR2GRAY
    )

    score = float(
        np.mean(difference)
    )

    return (
        difference,
        score
    )


# ================================================================
# LOCAL ELA
# ================================================================

def _local_ela(
    ela,
    document_box
):
    """
    Analyze ELA in meaningful blocks instead of individual pixels.

    This is the major change that prevents tiny text/noise features
    from becoming suspicious regions.
    """

    x0, y0, w0, h0 = document_box

    roi = ela[
        y0:y0 + h0,
        x0:x0 + w0
    ]

    if roi.size == 0:
        return []

    height, width = roi.shape

    # ------------------------------------------------------------
    # Calculate robust statistics
    # ------------------------------------------------------------

    median = float(
        np.median(roi)
    )

    mad = float(
        np.median(
            np.abs(
                roi.astype(
                    np.float32
                )
                -
                median
            )
        )
    )

    robust_std = max(
        1.4826 * mad,
        1.0
    )

    # We deliberately use a relatively conservative threshold.
    threshold = max(
        median +
        4.0 * robust_std,
        5.0
    )

    # ------------------------------------------------------------
    # Smooth before thresholding
    # ------------------------------------------------------------

    smooth = cv2.GaussianBlur(
        roi,
        (9, 9),
        0
    )

    mask = np.where(
        smooth >= threshold,
        255,
        0
    ).astype(
        np.uint8
    )

    # ------------------------------------------------------------
    # Remove tiny ELA noise
    # ------------------------------------------------------------

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (9, 9)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []

    document_area = width * height

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        # --------------------------------------------------------
        # IMPORTANT:
        # Reject tiny regions.
        # --------------------------------------------------------

        if w < 25:
            continue

        if h < 15:
            continue

        if area < 500:
            continue

        if area > document_area * 0.30:
            continue

        region = roi[
            y:y + h,
            x:x + w
        ]

        if region.size == 0:
            continue

        local_mean = float(
            np.mean(region)
        )

        local_max = float(
            np.max(region)
        )

        # --------------------------------------------------------
        # Local score
        # --------------------------------------------------------

        excess = max(
            0,
            local_mean -
            median
        )

        score = (
            excess * 6
            +
            max(
                0,
                local_max -
                threshold
            ) * 1.5
        )

        score = min(
            score,
            100
        )

        if score < 25:
            continue

        regions.append({

            "x": x0 + x,

            "y": y0 + y,

            "width": w,

            "height": h,

            "area": area,

            "ela_score":
                round(
                    score,
                    2
                ),

            "ela_mean":
                round(
                    local_mean,
                    2
                ),

            "ela_max":
                round(
                    local_max,
                    2
                )
        })

    return regions


# ================================================================
# LOCAL TEXTURE
# ================================================================

def _texture_anomalies(
    image,
    document_box
):
    """
    Detect meaningful texture differences.

    Unlike the previous implementation, this works on larger
    regions and rejects tiny text/printing artifacts.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    x0, y0, w0, h0 = document_box

    roi = gray[
        y0:y0 + h0,
        x0:x0 + w0
    ]

    if roi.size == 0:
        return []

    # ------------------------------------------------------------
    # Local standard deviation
    # ------------------------------------------------------------

    roi_float = roi.astype(
        np.float32
    )

    mean = cv2.GaussianBlur(
        roi_float,
        (0, 0),
        7
    )

    squared = cv2.GaussianBlur(
        roi_float ** 2,
        (0, 0),
        7
    )

    variance = np.maximum(
        squared -
        mean ** 2,
        0
    )

    texture = np.sqrt(
        variance
    )

    # ------------------------------------------------------------
    # Compare against document-wide texture statistics
    # ------------------------------------------------------------

    median = float(
        np.median(texture)
    )

    mad = float(
        np.median(
            np.abs(
                texture -
                median
            )
        )
    )

    threshold = (
        median +
        4.0 *
        max(
            1.4826 * mad,
            1.0
        )
    )

    mask = np.where(
        texture > threshold,
        255,
        0
    ).astype(
        np.uint8
    )

    # Larger morphology intentionally removes individual letters.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (11, 11)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []

    document_area = (
        w0 *
        h0
    )

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        # --------------------------------------------------------
        # Ignore small text/noise regions.
        # --------------------------------------------------------

        if w < 30:
            continue

        if h < 20:
            continue

        if area < 700:
            continue

        if area > document_area * 0.20:
            continue

        local_texture = texture[
            y:y + h,
            x:x + w
        ]

        texture_mean = float(
            np.mean(
                local_texture
            )
        )

        difference = abs(
            texture_mean -
            median
        )

        score = min(
            100,
            difference * 5
        )

        if score < 30:
            continue

        regions.append({

            "x": x0 + x,

            "y": y0 + y,

            "width": w,

            "height": h,

            "area": area,

            "texture_score":
                round(
                    score,
                    2
                ),

            "texture_mean":
                round(
                    texture_mean,
                    2
                )
        })

    return regions


# ================================================================
# BRIGHT / COVERING DETECTION
# ================================================================

def _covering_regions(
    image,
    document_box
):
    """
    Detect large, unusually bright, relatively uniform regions.

    This is useful for white covering/redaction-like edits.

    Small white text or highlights are ignored.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    x0, y0, w0, h0 = document_box

    roi = gray[
        y0:y0 + h0,
        x0:x0 + w0
    ]

    if roi.size == 0:
        return []

    # ------------------------------------------------------------
    # Adaptive brightness threshold
    # ------------------------------------------------------------

    threshold = max(
        220,
        int(
            np.percentile(
                roi,
                97
            )
        )
    )

    mask = cv2.inRange(
        roi,
        threshold,
        255
    )

    # Join nearby bright pixels.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (9, 9)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []

    document_area = (
        w0 *
        h0
    )

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        # --------------------------------------------------------
        # A meaningful covering should be reasonably large.
        # --------------------------------------------------------

        if w < 30:
            continue

        if h < 15:
            continue

        if area < 500:
            continue

        if area > document_area * 0.12:
            continue

        region = roi[
            y:y + h,
            x:x + w
        ]

        if region.size == 0:
            continue

        brightness = float(
            np.mean(region)
        )

        variation = float(
            np.std(region)
        )

        rectangularity = (
            cv2.contourArea(
                contour
            )
            /
            max(area, 1)
        )

        # --------------------------------------------------------
        # Scoring
        # --------------------------------------------------------

        score = 0

        if brightness >= 245:
            score += 35

        elif brightness >= 235:
            score += 25

        else:
            score += 15

        if variation < 20:
            score += 35

        elif variation < 35:
            score += 25

        elif variation < 50:
            score += 15

        if rectangularity >= 0.70:
            score += 30

        elif rectangularity >= 0.50:
            score += 20

        elif rectangularity >= 0.30:
            score += 10

        score = min(
            score,
            100
        )

        # --------------------------------------------------------
        # Do not automatically call this suspicious.
        # It is supporting evidence.
        # --------------------------------------------------------

        if score < 35:
            continue

        regions.append({

            "x": x0 + x,

            "y": y0 + y,

            "width": w,

            "height": h,

            "area": area,

            "brightness":
                round(
                    brightness,
                    2
                ),

            "variation":
                round(
                    variation,
                    2
                ),

            "rectangularity":
                round(
                    rectangularity,
                    3
                ),

            "covering_score":
                score
        })

    return regions


# ================================================================
# RECTANGLE DETECTION
# ================================================================

def _rectangle_regions(
    image,
    document_box
):
    """
    Detect large rectangular structures.

    IMPORTANT:
    A rectangle alone is NOT suspicious.

    It only provides supporting evidence when it overlaps another
    forensic anomaly.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    x0, y0, w0, h0 = document_box

    roi = gray[
        y0:y0 + h0,
        x0:x0 + w0
    ]

    edges = cv2.Canny(
        roi,
        60,
        160
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (7, 7)
    )

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []

    document_area = (
        w0 *
        h0
    )

    for contour in contours:

        perimeter = cv2.arcLength(
            contour,
            True
        )

        if perimeter <= 0:
            continue

        approximation = cv2.approxPolyDP(
            contour,
            0.03 * perimeter,
            True
        )

        if len(
            approximation
        ) < 4:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        if w < 40 or h < 25:
            continue

        if area < 1200:
            continue

        if area > document_area * 0.20:
            continue

        aspect = (
            max(w, h) /
            max(
                min(w, h),
                1
            )
        )

        if aspect > 10:
            continue

        contour_area = cv2.contourArea(
            contour
        )

        rectangularity = (
            contour_area /
            max(area, 1)
        )

        if rectangularity < 0.35:
            continue

        regions.append({

            "x": x0 + x,

            "y": y0 + y,

            "width": w,

            "height": h,

            "area": area,

            "rectangularity":
                round(
                    rectangularity,
                    3
                )
        })

    return regions[:30]


# ================================================================
# MERGE EVIDENCE
# ================================================================

def _combine_evidence(
    ela_regions,
    texture_regions,
    covering_regions,
    rectangle_regions
):
    """
    Combine independent forensic signals.

    Important:
        rectangle alone = NOT suspicious
        texture alone = weak
        covering alone = supporting evidence
        ELA + another signal = stronger evidence
    """

    candidates = []

    # ------------------------------------------------------------
    # Start with ELA regions
    # ------------------------------------------------------------

    for region in ela_regions:

        candidates.append({

            "x": region["x"],

            "y": region["y"],

            "width": region["width"],

            "height": region["height"],

            "ela_score":
                region[
                    "ela_score"
                ],

            "texture_score": 0,

            "covering_score": 0,

            "rectangular_score": 0
        })

    # ------------------------------------------------------------
    # Helper to match regions
    # ------------------------------------------------------------

    def find_match(region):

        target = (
            region["x"],
            region["y"],
            region["width"],
            region["height"]
        )

        best = None
        best_iou = 0

        for candidate in candidates:

            box = (
                candidate["x"],
                candidate["y"],
                candidate["width"],
                candidate["height"]
            )

            overlap = _iou(
                target,
                box
            )

            if overlap > best_iou:

                best_iou = overlap
                best = candidate

        # We allow nearby regions because different detectors
        # rarely produce identical boxes.
        if best_iou >= 0.15:
            return best

        return None

    # ------------------------------------------------------------
    # Texture
    # ------------------------------------------------------------

    for region in texture_regions:

        match = find_match(
            region
        )

        if match is not None:

            match[
                "texture_score"
            ] = region[
                "texture_score"
            ]

        else:

            # Texture-only candidates are deliberately weak.
            candidates.append({

                "x": region["x"],

                "y": region["y"],

                "width": region["width"],

                "height": region["height"],

                "ela_score": 0,

                "texture_score":
                    region[
                        "texture_score"
                    ],

                "covering_score": 0,

                "rectangular_score": 0
            })

    # ------------------------------------------------------------
    # Covering
    # ------------------------------------------------------------

    for region in covering_regions:

        match = find_match(
            region
        )

        if match is not None:

            match[
                "covering_score"
            ] = region[
                "covering_score"
            ]

        else:

            candidates.append({

                "x": region["x"],

                "y": region["y"],

                "width": region["width"],

                "height": region["height"],

                "ela_score": 0,

                "texture_score": 0,

                "covering_score":
                    region[
                        "covering_score"
                    ],

                "rectangular_score": 0
            })

    # ------------------------------------------------------------
    # Rectangle
    # ------------------------------------------------------------

    for region in rectangle_regions:

        match = find_match(
            region
        )

        if match is not None:

            match[
                "rectangular_score"
            ] = round(
                region[
                    "rectangularity"
                ] * 100,
                2
            )

    # ------------------------------------------------------------
    # Calculate final local evidence
    # ------------------------------------------------------------

    final = []

    for candidate in candidates:

        ela = candidate[
            "ela_score"
        ]

        texture = candidate[
            "texture_score"
        ]

        covering = candidate[
            "covering_score"
        ]

        rectangle = candidate[
            "rectangular_score"
        ]

        evidence = []

        # --------------------------------------------------------
        # ELA is the primary signal.
        # --------------------------------------------------------

        if ela >= 35:

            evidence.append(
                "ELA"
            )

        # Texture is supporting evidence.
        if texture >= 50:

            evidence.append(
                "TEXTURE"
            )

        # Covering is supporting evidence.
        if covering >= 50:

            evidence.append(
                "COVERING"
            )

        # Rectangle is only supporting evidence.
        if rectangle >= 65:

            evidence.append(
                "RECTANGLE"
            )

        # --------------------------------------------------------
        # Determine number of independent signals.
        # --------------------------------------------------------

        independent_signals = 0

        if ela >= 35:
            independent_signals += 1

        if texture >= 50:
            independent_signals += 1

        if covering >= 50:
            independent_signals += 1

        # Rectangle doesn't count by itself.
        if (
            rectangle >= 65
            and independent_signals > 0
        ):
            independent_signals += 1

        # --------------------------------------------------------
        # LOCAL SCORE
        # --------------------------------------------------------

        if independent_signals == 0:

            # No meaningful evidence.
            continue

        # Primary signal.
        local_score = max(
            ela,
            texture * 0.60,
            covering * 0.70
        )

        # Multiple independent signals strengthen confidence.
        if independent_signals >= 2:

            local_score += 15

        if independent_signals >= 3:

            local_score += 10

        local_score = min(
            local_score,
            100
        )

        # --------------------------------------------------------
        # IMPORTANT:
        # One weak signal should not create a suspicious region.
        # --------------------------------------------------------

        if (
            local_score < 50
            and independent_signals < 2
        ):
            continue

        candidate[
            "local_score"
        ] = round(
            local_score,
            2
        )

        candidate[
            "evidence_count"
        ] = independent_signals

        candidate[
            "evidence"
        ] = evidence

        final.append(
            candidate
        )

    # ------------------------------------------------------------
    # Sort by strongest evidence
    # ------------------------------------------------------------

    final.sort(
        key=lambda r:
        r["local_score"],
        reverse=True
    )

    # ------------------------------------------------------------
    # Remove heavily overlapping detections.
    # ------------------------------------------------------------

    selected = []

    for region in final:

        box = (
            region["x"],
            region["y"],
            region["width"],
            region["height"]
        )

        duplicate = False

        for existing in selected:

            existing_box = (
                existing["x"],
                existing["y"],
                existing["width"],
                existing["height"]
            )

            if _iou(
                box,
                existing_box
            ) > 0.35:

                duplicate = True
                break

        if not duplicate:

            selected.append(
                region
            )

    return selected[:10]


# ================================================================
# MAIN FUNCTION
# ================================================================

def perform_ela(
    image_path,
    output_path="ela_result.jpg"
):
    """
    Document-aware ELA and localized forensic analysis.

    Compatible with the existing analyzer.py.

    Returns JSON-compatible dictionaries/lists.
    """

    # ============================================================
    # LOAD IMAGE
    # ============================================================

    image = cv2.imread(
        image_path
    )

    if image is None:

        return {

            "success": False,

            "message":
                "Could not read image"
        }

    height, width = image.shape[:2]

    # ============================================================
    # FIND DOCUMENT
    # ============================================================

    document_box = (
        _find_document_area(
            image
        )
    )

    # ============================================================
    # GLOBAL ELA
    # ============================================================

    ela, global_score = (
        _global_ela(
            image
        )
    )

    if ela is None:

        return {

            "success": False,

            "message":
                "ELA calculation failed"
        }

    # ============================================================
    # LOCAL ELA
    # ============================================================

    ela_regions = (
        _local_ela(
            ela,
            document_box
        )
    )

    # ============================================================
    # TEXTURE
    # ============================================================

    texture_regions = (
        _texture_anomalies(
            image,
            document_box
        )
    )

    # ============================================================
    # COVERING
    # ============================================================

    covering_regions = (
        _covering_regions(
            image,
            document_box
        )
    )

    # ============================================================
    # RECTANGLES
    # ============================================================

    rectangle_regions = (
        _rectangle_regions(
            image,
            document_box
        )
    )

    # ============================================================
    # COMBINE
    # ============================================================

    combined = (
        _combine_evidence(
            ela_regions,
            texture_regions,
            covering_regions,
            rectangle_regions
        )
    )

    # ============================================================
    # SUSPICIOUS REGIONS
    # ============================================================

    suspicious_regions = [
        region
        for region in combined
        if region[
            "local_score"
        ] >= 50
    ]

    localized_suspicious = (
        len(
            suspicious_regions
        ) > 0
    )

    # ============================================================
    # MAX LOCAL SCORE
    # ============================================================

    if combined:

        max_local_score = max(
            region[
                "local_score"
            ]
            for region in combined
        )

    else:

        max_local_score = 0

    # ============================================================
    # COVERING SUMMARY
    # ============================================================

    strong_covering = [
        region
        for region
        in covering_regions
        if region[
            "covering_score"
        ] >= 60
    ]

    covering_suspicious = (
        len(
            strong_covering
        ) > 0
    )

    if covering_regions:

        max_covering_score = max(
            region[
                "covering_score"
            ]
            for region
            in covering_regions
        )

    else:

        max_covering_score = 0

    # ============================================================
    # CREATE OUTPUT PATHS
    # ============================================================

    _ensure_directory(
        output_path
    )

    base, _ = os.path.splitext(
        output_path
    )

    mask_output = (
        base +
        "_mask.png"
    )

    regions_output = (
        base +
        "_regions.jpg"
    )

    document_output = (
        base +
        "_document.jpg"
    )

    # ============================================================
    # ELA VISUALIZATION
    # ============================================================

    ela_visual = cv2.normalize(
        ela,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    cv2.imwrite(
        output_path,
        ela_visual
    )

    # ============================================================
    # CREATE DOCUMENT MASK
    # ============================================================

    document_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    x, y, w, h = document_box

    document_mask[
        y:y + h,
        x:x + w
    ] = 255

    cv2.imwrite(
        document_output,
        document_mask
    )

    # ============================================================
    # LOCAL ELA MASK
    # ============================================================

    local_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    for region in ela_regions:

        rx = region["x"]
        ry = region["y"]
        rw = region["width"]
        rh = region["height"]

        cv2.rectangle(
            local_mask,
            (rx, ry),
            (
                rx + rw,
                ry + rh
            ),
            255,
            -1
        )

    cv2.imwrite(
        mask_output,
        local_mask
    )

    # ============================================================
    # CREATE FORENSIC OVERLAY
    # ============================================================

    overlay = image.copy()

    # Document boundary in blue.
    cv2.rectangle(
        overlay,
        (
            document_box[0],
            document_box[1]
        ),
        (
            document_box[0] +
            document_box[2],
            document_box[1] +
            document_box[3]
        ),
        (255, 0, 0),
        2
    )

    # Suspicious regions.
    for region in combined:

        rx = region["x"]
        ry = region["y"]
        rw = region["width"]
        rh = region["height"]

        score = region[
            "local_score"
        ]

        label = (
            f"{score:.0f}:"
            +
            ",".join(
                region[
                    "evidence"
                ]
            )
        )

        # Strong evidence.
        if score >= 70:

            thickness = 3

        else:

            thickness = 2

        cv2.rectangle(
            overlay,
            (rx, ry),
            (
                rx + rw,
                ry + rh
            ),
            (0, 0, 255),
            thickness
        )

        cv2.putText(
            overlay,
            label,
            (
                rx,
                max(
                    15,
                    ry - 5
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (0, 0, 255),
            1,
            cv2.LINE_AA
        )

    cv2.imwrite(
        regions_output,
        overlay
    )

    # ============================================================
    # FINAL RESULT
    # ============================================================

    return {

        "success": True,

        "score":
            round(
                global_score,
                2
            ),

        "image_width":
            width,

        "image_height":
            height,

        "document_area": {

            "x":
                int(
                    document_box[0]
                ),

            "y":
                int(
                    document_box[1]
                ),

            "width":
                int(
                    document_box[2]
                ),

            "height":
                int(
                    document_box[3]
                )
        },

        "localized_suspicious":
            localized_suspicious,

        "suspicious_regions":
            len(
                suspicious_regions
            ),

        "max_local_score":
            round(
                max_local_score,
                2
            ),

        "covering_suspicious":
            covering_suspicious,

        "covering_regions":
            len(
                covering_regions
            ),

        "max_covering_score":
            round(
                max_covering_score,
                2
            ),

        "regions":
            combined,

        "output":
            output_path,

        "mask_output":
            mask_output,

        "regions_output":
            regions_output,

        "document_output":
            document_output
    }