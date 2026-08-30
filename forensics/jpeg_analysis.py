import os
import cv2
import numpy as np


def analyze_jpeg(image_path, output_dir="working"):
    """
    Analyze local 8x8 DCT block energy behavior.

    Global JPEG texture/variation is not considered manipulation by itself.
    A suspicious result requires a compact interior cluster of anomalous
    blocks. This prevents ordinary text-heavy documents from being flagged.

    Returns a JSON-compatible dictionary.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return {"success": False, "error": "Unable to read image"}

        original_h, original_w = image.shape
        h = (original_h // 8) * 8
        w = (original_w // 8) * 8
        image = image[:h, :w]

        if h < 64 or w < 64:
            return {"success": False, "error": "Image too small"}

        gx = cv2.Sobel(image, cv2.CV_32F, 1, 0)
        gy = cv2.Sobel(image, cv2.CV_32F, 0, 1)
        grad = cv2.magnitude(gx, gy)

        rows, cols = h // 8, w // 8
        energy = np.zeros((rows, cols), np.float32)
        norm_energy = np.zeros((rows, cols), np.float32)

        for r in range(rows):
            for c in range(cols):
                block = image[r * 8:(r + 1) * 8, c * 8:(c + 1) * 8].astype(np.float32)
                block_g = grad[r * 8:(r + 1) * 8, c * 8:(c + 1) * 8]
                block -= block.mean()
                dct = cv2.dct(block)
                e = float(np.mean(np.abs(dct.flatten()[1:])))
                energy[r, c] = e
                norm_energy[r, c] = e / (float(np.mean(block_g)) + 2.0)

        values = energy.ravel()
        mean_value = float(np.mean(values))
        std_value = float(np.std(values))

        norm_values = norm_energy.ravel()
        median_norm = float(np.median(norm_values))
        mad_norm = float(np.median(np.abs(norm_values - median_norm)))
        robust_scale = max(1.4826 * mad_norm, 0.05)
        z = np.abs(norm_energy - median_norm) / robust_scale

        # Local relative difference from 4-neighbor median
        local_diff = np.zeros_like(norm_energy)
        for r in range(rows):
            for c in range(cols):
                neighbors = []
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        neighbors.append(float(norm_energy[rr, cc]))
                if neighbors:
                    med_n = float(np.median(neighbors))
                    local_diff[r, c] = abs(float(norm_energy[r, c]) - med_n) / max(abs(med_n), 1.0)

        # Candidate blocks: robust outlier AND locally inconsistent
        mask = ((z >= 5.5) & (local_diff >= 1.2)).astype(np.uint8)

        # Ignore outer 2-block document frame
        mask[:2, :] = 0
        mask[-2:, :] = 0
        mask[:, :2] = 0
        mask[:, -2:] = 0

        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

        nlabels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        components = []
        for label in range(1, nlabels):
            area = int(stats[label, cv2.CC_STAT_AREA])
            x = int(stats[label, cv2.CC_STAT_LEFT])
            y = int(stats[label, cv2.CC_STAT_TOP])
            ww = int(stats[label, cv2.CC_STAT_WIDTH])
            hh = int(stats[label, cv2.CC_STAT_HEIGHT])
            if area >= 12 and ww * hh <= max(16, int(rows * cols * 0.08)):
                components.append((area, x, y, ww, hh))

        components.sort(reverse=True)
        suspicious_blocks = int(mask.sum())
        total_blocks = int(rows * cols)
        suspicious_ratio = float(suspicious_blocks / max(total_blocks, 1))

        local_values = local_diff.ravel()
        local_mean = float(np.mean(local_values))
        local_median = float(np.median(local_values))
        local_high_ratio = float(np.mean(local_values >= 0.60))
        local_strong_ratio = float(np.mean(local_values >= 1.0))

        variation = float(std_value / max(abs(mean_value), 1e-6))
        global_score = min(100.0, variation * 100.0)

        largest_component = components[0][0] if components else 0
        compact_component = bool(components and largest_component >= 16)
        sparse_localized = bool(0.001 <= suspicious_ratio <= 0.05)

        suspicious = bool(
            compact_component
            and sparse_localized
            and local_strong_ratio >= 0.015
        )

        evidence = []
        if suspicious:
            evidence.append("Localized JPEG block-level inconsistency detected")
        elif global_score >= 60.0:
            evidence.append("Global JPEG texture variation observed; not treated as fraud without localized evidence")

        # Visualization
        visualization = cv2.normalize(energy, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        visualization = cv2.resize(visualization, (w, h), interpolation=cv2.INTER_NEAREST)
        visualization = cv2.cvtColor(visualization, cv2.COLOR_GRAY2BGR)

        for area, x, y, ww, hh in components[:30]:
            cv2.rectangle(
                visualization,
                (x * 8, y * 8),
                ((x + ww) * 8, (y + hh) * 8),
                (0, 0, 255), 1
            )

        name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"jpeg_{name}.png")
        cv2.imwrite(output_path, visualization)

        jpeg_score = 0.0
        if suspicious:
            jpeg_score = min(
                100.0,
                max(50.0, global_score * 0.40 + min(local_strong_ratio * 300.0, 35.0))
            )

        return {
            "success": True,
            "jpeg_score": round(float(jpeg_score), 2),
            "variation": round(float(variation), 4),
            "mean_block_energy": round(mean_value, 4),
            "std_block_energy": round(std_value, 4),
            "local_inconsistency": round(local_mean, 4),
            "local_median_difference": round(local_median, 4),
            "local_high_ratio": round(local_high_ratio, 4),
            "local_strong_ratio": round(local_strong_ratio, 4),
            "suspicious_blocks": int(suspicious_blocks),
            "total_blocks": int(total_blocks),
            "suspicious_block_ratio": round(float(suspicious_ratio), 4),
            "localized_components": int(len(components)),
            "largest_component": int(largest_component),
            "suspicious": suspicious,
            "evidence": evidence,
            "output": output_path
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
