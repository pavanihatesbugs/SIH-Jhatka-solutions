import os
import cv2
import numpy as np


def analyze_noise(image_path, output_path="working/noise_result.png"):
    """
    Analyze image noise level and spatial noise variance consistency.

    Natural scans/photographs exhibit uniform noise across the document surface.
    Manipulated areas (such as pasted patches or inpainting) often display
    local noise variance discontinuities relative to the surrounding image.

    Returns a JSON-compatible dictionary.
    """
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        image = cv2.imread(image_path)
        if image is None:
            return {"success": False, "error": "Could not read image"}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        if h < 32 or w < 32:
            return {"success": False, "error": "Image too small for noise analysis"}

        # Estimate smooth background and noise residual
        smooth = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = cv2.absdiff(gray, smooth).astype(np.float32)

        # High-contrast normalized noise visualization map
        noise_map = cv2.normalize(noise, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        cv2.imwrite(output_path, noise_map)

        # Global average noise level
        noise_score = float(np.mean(noise))

        # Measure spatial noise consistency across non-overlapping blocks
        block_size = max(16, min(h, w) // 25)
        rows, cols = h // block_size, w // block_size

        block_variances = []
        for r in range(rows):
            for c in range(cols):
                block = noise[r * block_size:(r + 1) * block_size, c * block_size:(c + 1) * block_size]
                if block.size > 0:
                    block_variances.append(float(np.var(block)))

        if len(block_variances) >= 6:
            v_arr = np.array(block_variances)
            median_var = float(np.median(v_arr))
            mad_var = float(np.median(np.abs(v_arr - median_var)))
            robust_sigma = max(1.4826 * mad_var, 0.5)

            # Local step differences across adjacent block grid
            grid = v_arr.reshape((rows, cols))
            local_diffs = []
            for r in range(1, rows - 1):
                for c in range(1, cols - 1):
                    neighbors = [grid[r - 1, c], grid[r + 1, c], grid[r, c - 1], grid[r, c + 1]]
                    diff = abs(grid[r, c] - np.median(neighbors))
                    local_diffs.append(diff)

            max_local_diff = float(np.max(local_diffs)) if local_diffs else 0.0
            noise_inconsistency = float(max_local_diff / robust_sigma)
        else:
            median_var = float(np.var(noise))
            noise_inconsistency = 0.0

        # Conservative suspicion threshold: genuine camera/scan photos have noise
        # but uniform texture; an injected or inconsistent noise patch produces sharp variance steps.
        suspicious = bool(noise_inconsistency >= 12.0 and noise_score >= 4.0)

        evidence = []
        if suspicious:
            evidence.append("Localized noise variance inconsistency detected")

        return {
            "success": True,
            "noise_score": round(noise_score, 2),
            "noise_inconsistency": round(noise_inconsistency, 2),
            "median_variance": round(median_var, 2),
            "suspicious": suspicious,
            "evidence": evidence,
            "output": output_path
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
