import os
import cv2
import numpy as np


def is_standard_layout_element(x, y, ww, hh, img_w, img_h):
    """
    Check if a rectangular contour corresponds to standard ID card layout
    elements (such as an ID photo frame, header banner, or signature box).
    """
    aspect = float(ww / float(max(hh, 1)))
    area_ratio = float((ww * hh) / float(img_w * img_h))

    # Standard ID photo frame: roughly square, located near left or right margin
    is_square_photo = (
        (0.70 <= aspect <= 1.40)
        and ((x < 0.32 * img_w) or ((x + ww) > 0.60 * img_w))
        and (0.03 <= area_ratio <= 0.22)
    )

    # Standard header banner: top 20% of card or high aspect ratio banner
    is_header = (y < 0.20 * img_h) or (aspect >= 3.0 and hh <= 48)

    # Standard bottom signature banner: bottom 22% of card
    is_signature_box = ((y + hh) > 0.78 * img_h) and (aspect >= 2.5)

    return is_square_photo or is_header or is_signature_box


def analyze_edges(image_path, output_dir="working"):
    """
    Detect unusual internal rectangular boundaries as supporting evidence.

    Identifies localized inserted patches or covering operations. Standard
    document structures (e.g. ID photo frames, header text boxes) are recognized
    and not marked as standalone fraud evidence.

    Returns a JSON-compatible dictionary.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return {"success": False, "error": "Unable to read image"}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        image_area = float(h * w)

        if h < 60 or w < 60:
            return {"success": False, "error": "Image too small for edge analysis"}

        smooth = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(smooth, 20, 60)

        closed = cv2.morphologyEx(
            edges,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        )
        contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        for contour in contours:
            x, y, ww, hh = cv2.boundingRect(contour)
            area = ww * hh
            area_ratio = float(area / image_area)

            if area < 600 or ww < 25 or hh < 18:
                continue
            if area_ratio < 0.002 or area_ratio > 0.25:
                continue
            # Ignore outer document boundary frame
            if x <= 10 and y <= 10 and x + ww >= w - 10 and y + hh >= h - 10:
                continue

            contour_area = float(cv2.contourArea(contour))
            rectangularity = float(contour_area / max(float(area), 1.0))
            aspect = float(ww / float(max(hh, 1)))

            roi = edges[y:y + hh, x:x + ww]
            edge_density = float(np.mean(roi > 0)) if roi.size else 0.0

            # Boundary edge concentration along the 4 border sides
            band = max(2, min(6, int(min(ww, hh) * 0.05)))
            side_values = [
                float(np.mean(edges[y:y + band, x:x + ww] > 0)),
                float(np.mean(edges[y + hh - band:y + hh, x:x + ww] > 0)),
                float(np.mean(edges[y:y + hh, x:x + band] > 0)),
                float(np.mean(edges[y:y + hh, x + ww - band:x + ww] > 0)),
            ]
            strong_sides = sum(v >= 0.12 for v in side_values)
            border_strength = float(np.mean(side_values))

            # Interior vs surrounding exterior contrast
            pad = max(6, min(24, int(min(ww, hh) * 0.12)))
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(w, x + ww + pad), min(h, y + hh + pad)
            outer = gray[y1:y2, x1:x2]
            mask = np.ones(outer.shape, bool)
            ix1, iy1 = x - x1, y - y1
            mask[iy1:iy1 + hh, ix1:ix1 + ww] = False
            ring = outer[mask]

            interior = gray[y + 2:y + hh - 2, x + 2:x + ww - 2]
            int_mean = float(np.mean(interior)) if interior.size else float(np.mean(gray[y:y + hh, x:x + ww]))
            ext_mean = float(np.mean(ring)) if ring.size else int_mean
            int_std = float(np.std(interior)) if interior.size else 0.0
            ext_std = float(np.std(ring)) if ring.size else 0.0

            color_diff = abs(int_mean - ext_mean)
            texture_diff = abs(int_std - ext_std)

            is_standard = is_standard_layout_element(x, y, ww, hh, w, h)

            score = 0.0
            if rectangularity >= 0.85:
                score += 25
            elif rectangularity >= 0.70:
                score += 15

            if strong_sides >= 4:
                score += 25
            elif strong_sides >= 3:
                score += 15
            elif strong_sides >= 2:
                score += 8

            if border_strength >= 0.20:
                score += 20
            elif border_strength >= 0.10:
                score += 10

            if color_diff >= 30.0:
                score += 25
            elif color_diff >= 15.0:
                score += 12

            if texture_diff >= 15.0:
                score += 10

            if is_standard:
                score = max(0.0, score - 35.0)

            score = min(100.0, score)

            high_confidence = bool(
                score >= 65.0
                and strong_sides >= 3
                and rectangularity >= 0.75
                and not is_standard
                and (color_diff >= 20.0 or border_strength >= 0.18)
            )

            regions.append({
                "x": int(x),
                "y": int(y),
                "width": int(ww),
                "height": int(hh),
                "score": int(round(score)),
                "rectangularity": round(rectangularity, 3),
                "aspect_ratio": round(aspect, 3),
                "strong_sides": int(strong_sides),
                "border_strength": round(border_strength, 4),
                "color_diff": round(color_diff, 2),
                "is_standard_layout": bool(is_standard),
                "high_confidence": high_confidence
            })

        regions.sort(key=lambda r: r["score"], reverse=True)
        high = [r for r in regions if r["high_confidence"]]

        suspicious = bool(high and len(high) <= 6)
        selected = high[:15] if suspicious else regions[:5]
        max_score = max((r["score"] for r in selected), default=0)

        # Draw visualization
        output = image.copy()
        for r in selected:
            x, y, ww, hh = r["x"], r["y"], r["width"], r["height"]
            color = (0, 0, 255) if r.get("high_confidence") else (0, 200, 255)
            cv2.rectangle(output, (x, y), (x + ww, y + hh), color, 2)
            cv2.putText(
                output, f"edge {r['score']}", (x, max(18, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA
            )

        name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"edges_{name}.jpg")
        cv2.imwrite(output_path, output)

        evidence = ["Localized internal boundary anomaly detected"] if suspicious else []

        return {
            "success": True,
            "suspicious": suspicious,
            "regions": int(len(selected)),
            "high_confidence_regions": int(len(high)),
            "max_edge_score": int(max_score),
            "details": selected,
            "evidence": evidence,
            "output": output_path
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
