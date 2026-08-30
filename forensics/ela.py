import os
import cv2
import numpy as np


JPEG_QUALITY = 90
MIN_REGION_AREA = 120
MAX_REGION_FRACTION = 0.15


def get_document_area(image):
    height, width = image.shape[:2]
    margin_x = max(int(width * 0.02), 2)
    margin_y = max(int(height * 0.02), 2)
    return {
        "x": margin_x,
        "y": margin_y,
        "width": width - 2 * margin_x,
        "height": height - 2 * margin_y
    }


def generate_ela(image):
    success, encoded = cv2.imencode(
        ".jpg",
        image,
        [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    )
    if not success:
        return None

    recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if recompressed is None:
        return None

    difference = cv2.absdiff(image, recompressed)
    difference_gray = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
    difference_smooth = cv2.GaussianBlur(difference_gray, (3, 3), 0)

    visual = np.clip(difference_gray.astype(np.float32) * 12.0, 0, 255).astype(np.uint8)

    return {
        "raw": difference_smooth,
        "visual": visual
    }


def find_suspicious_regions(image, ela_raw, document_area):
    height, width = ela_raw.shape
    x0, y0 = document_area["x"], document_area["y"]
    w0, h0 = document_area["width"], document_area["height"]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    grad = cv2.magnitude(gx, gy)

    # Gradient compensation: suppress normal printed font edge ELA
    ela_residual = np.maximum(0, ela_raw.astype(np.float32) - grad * 0.08)
    smooth_res = cv2.GaussianBlur(ela_residual, (5, 5), 0)

    doc_res = smooth_res[y0:y0 + h0, x0:x0 + w0]
    mean_r = float(np.mean(doc_res))
    std_r = float(np.std(doc_res))

    thresh = max(2.5, mean_r + 3.0 * std_r)
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[y0:y0 + h0, x0:x0 + w0] = (
        smooth_res[y0:y0 + h0, x0:x0 + w0] >= thresh
    ).astype(np.uint8) * 255

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    nlabels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    image_area = width * height

    regions = []
    for label in range(1, nlabels):
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w = int(stats[label, cv2.CC_STAT_WIDTH])
        h = int(stats[label, cv2.CC_STAT_HEIGHT])
        area = int(stats[label, cv2.CC_STAT_AREA])

        if area < MIN_REGION_AREA or area > (image_area * MAX_REGION_FRACTION):
            continue
        if w < 15 or h < 12:
            continue

        # Ignore standard ID layout elements (header title banner or bottom footnote)
        if y < 0.20 * height or (y + h) > 0.88 * height:
            continue

        # Filter out normal thin horizontal printed text lines (height < 32 and high aspect)
        aspect = float(w / max(h, 1))
        if h < 32 and aspect > 2.8:
            continue

        region_mask = (labels[y:y + h, x:x + w] == label)
        if not np.any(region_mask):
            continue

        local_vals = ela_raw[y:y + h, x:x + w][region_mask].astype(np.float32)
        local_mean = float(np.mean(local_vals))
        local_max = float(np.max(local_vals))
        ela_contrast = local_mean / max(mean_r, 0.2)

        rect_score = 25 if (1.2 <= aspect <= 10 and w >= 25) else 0

        score_val = min(ela_contrast * 15.0, 60.0) + min(local_mean * 4.0, 20.0) + rect_score
        local_score = int(round(max(0.0, min(100.0, score_val))))

        suspicious = bool(local_score >= 45 and area >= 120)
        covering_like = bool(rect_score >= 25 and suspicious)

        evidence = []
        if suspicious:
            evidence.append("Localized ELA compression inconsistency detected")

        regions.append({
            "x": x, "y": y, "width": w, "height": h, "area": area,
            "ela_score": round(local_mean, 2),
            "max_ela": round(local_max, 2),
            "ela_contrast": round(ela_contrast, 2),
            "local_score": local_score,
            "suspicious": suspicious,
            "covering_like": covering_like,
            "evidence": evidence
        })

    return regions


def draw_regions(image, regions):
    output = image.copy()
    for region in regions:
        if not region["suspicious"] and not region.get("covering_like"):
            continue
        x, y, w, h = region["x"], region["y"], region["width"], region["height"]
        score = region["local_score"]
        color = (0, 0, 255) if region["suspicious"] else (0, 165, 255)
        cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            output, f"ELA={score}", (x, max(15, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA
        )
    return output


def perform_ela(image_path, output_path="working/ela_result.png"):
    """
    Perform Error Level Analysis (ELA) on an image.

    Saves visualization outputs to disk and returns a JSON-compatible dictionary.
    """
    try:
        if not os.path.exists(image_path):
            return {"success": False, "error": "Image file not found"}

        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return {"success": False, "error": "Unable to read image"}

        h, w = image.shape[:2]
        doc_area = get_document_area(image)
        ela_res = generate_ela(image)
        if ela_res is None:
            return {"success": False, "error": "ELA generation failed"}

        ela_raw = ela_res["raw"]
        ela_visual = ela_res["visual"]

        dx, dy, dw, dh = doc_area["x"], doc_area["y"], doc_area["width"], doc_area["height"]
        doc_pixels = ela_raw[dy:dy + dh, dx:dx + dw]
        global_score = float(np.mean(doc_pixels))

        regions = find_suspicious_regions(image, ela_raw, doc_area)
        suspicious_regions = [r for r in regions if r["suspicious"]]
        covering_regions = [r for r in regions if r.get("covering_like")]

        max_local_score = max((r["local_score"] for r in suspicious_regions), default=0)
        max_covering_score = max((r["local_score"] for r in covering_regions), default=0)

        out_dir = os.path.dirname(output_path) or "."
        os.makedirs(out_dir, exist_ok=True)
        cv2.imwrite(output_path, ela_visual)

        base_no_ext, _ = os.path.splitext(output_path)
        mask_output = f"{base_no_ext}_mask.png"
        regions_output = f"{base_no_ext}_regions.jpg"

        mask = np.zeros((h, w), dtype=np.uint8)
        for r in suspicious_regions:
            cv2.rectangle(mask, (r["x"], r["y"]), (r["x"] + r["width"], r["y"] + r["height"]), 255, -1)
        cv2.imwrite(mask_output, mask)

        region_image = draw_regions(image, regions)
        cv2.imwrite(regions_output, region_image)

        return {
            "success": True,
            "global_score": round(global_score, 2),
            "score": round(global_score, 2),
            "image_width": int(w),
            "image_height": int(h),
            "document_area": doc_area,
            "localized_suspicious": bool(len(suspicious_regions) > 0),
            "suspicious_regions": int(len(suspicious_regions)),
            "max_local_score": int(max_local_score),
            "covering_suspicious": bool(len(covering_regions) > 0),
            "covering_regions": int(len(covering_regions)),
            "max_covering_score": int(max_covering_score),
            "regions": regions,
            "output": output_path,
            "mask_output": mask_output,
            "regions_output": regions_output
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
