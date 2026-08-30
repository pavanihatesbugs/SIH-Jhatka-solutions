import os
from collections import Counter
import cv2
import numpy as np


def detect_copy_move(image_path, output_path="working/copy_move_result.png"):
    """
    Detect possible copy-move image duplication from spatially separated feature matches.

    Identifies clusters of feature pairs sharing consistent spatial displacement
    and confirms geometric consistency via RANSAC affine transformation.

    Returns a JSON-compatible dictionary.
    """
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return {"success": False, "error": "Could not read image"}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        scale = min(1.0, 1400.0 / max(gray.shape))
        work = cv2.resize(gray, None, fx=scale, fy=scale) if scale < 1.0 else gray

        orb = cv2.ORB_create(
            nfeatures=3000,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=15,
            patchSize=31,
            fastThreshold=10
        )
        keypoints, descriptors = orb.detectAndCompute(work, None)

        output = image.copy()
        if descriptors is None or len(keypoints) < 15:
            cv2.imwrite(output_path, output)
            return {
                "success": True,
                "keypoints": int(len(keypoints)) if keypoints is not None else 0,
                "matches": 0,
                "inliers": 0,
                "suspicious": False,
                "evidence": [],
                "output": output_path
            }

        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        knn = matcher.knnMatch(descriptors, descriptors, k=min(5, len(descriptors)))

        candidates = []
        min_sep = max(30.0, min(work.shape) * 0.03)

        for qi, row in enumerate(knn):
            nonself = [m for m in row if m.trainIdx != qi]
            if not nonself:
                continue
            best = nonself[0]
            second = nonself[1] if len(nonself) > 1 else None
            if best.distance > 45:
                continue
            if second is not None and best.distance >= 0.85 * second.distance:
                continue

            p1 = np.array(keypoints[qi].pt, dtype=np.float32)
            p2 = np.array(keypoints[best.trainIdx].pt, dtype=np.float32)
            d = p2 - p1
            dist = float(np.linalg.norm(d))
            if dist < min_sep:
                continue
            candidates.append((qi, best.trainIdx, float(best.distance), p1, p2, d))

        # Filter unique descriptor pairs
        unique = {}
        for item in candidates:
            key = tuple(sorted((item[0], item[1])))
            if key not in unique or item[2] < unique[key][2]:
                unique[key] = item
        candidates = list(unique.values())

        if not candidates:
            cv2.imwrite(output_path, output)
            return {
                "success": True,
                "keypoints": int(len(keypoints)),
                "matches": 0,
                "inliers": 0,
                "suspicious": False,
                "evidence": [],
                "output": output_path
            }

        # Cluster displacement vectors into spatial bins
        bin_size = max(10.0, min(work.shape) * 0.015)
        disp_bins = [
            (
                int(round(float(item[5][0]) / bin_size)),
                int(round(float(item[5][1]) / bin_size))
            )
            for item in candidates
        ]

        counts = Counter(disp_bins)
        ranked = counts.most_common(8)

        best_inliers = []
        best_ratio = 0.0
        best_disp = 0.0

        for best_bin, count in ranked:
            if count < 4:
                continue
            dominant = [
                item for item, b in zip(candidates, disp_bins)
                if b == best_bin
            ]

            inliers = dominant
            inlier_ratio = 1.0

            if len(dominant) >= 4:
                src = np.float32([x[3] for x in dominant]).reshape(-1, 1, 2)
                dst = np.float32([x[4] for x in dominant]).reshape(-1, 1, 2)
                _, mask = cv2.estimateAffinePartial2D(
                    src, dst,
                    method=cv2.RANSAC,
                    ransacReprojThreshold=6.0,
                    maxIters=2000,
                    confidence=0.98
                )
                if mask is not None:
                    mask = mask.ravel().astype(bool)
                    inliers = [dominant[i] for i, ok in enumerate(mask) if ok]
                    inlier_ratio = len(inliers) / max(len(dominant), 1)

            dx = float(best_bin[0] * bin_size)
            dy = float(best_bin[1] * bin_size)
            disp = float(np.hypot(dx, dy))

            if len(inliers) > len(best_inliers):
                best_inliers = inliers
                best_ratio = inlier_ratio
                best_disp = disp

        # Require a robust cluster with geometric transform consistency
        suspicious = bool(len(best_inliers) >= 6 and best_ratio >= 0.50 and best_disp >= min_sep)

        if best_inliers:
            for item in best_inliers[:100]:
                pt_a = tuple(np.round(item[3] / max(scale, 1e-9)).astype(int))
                pt_b = tuple(np.round(item[4] / max(scale, 1e-9)).astype(int))
                color = (0, 0, 255) if suspicious else (255, 180, 0)
                cv2.circle(output, pt_a, 4, color, 2)
                cv2.circle(output, pt_b, 4, color, 2)
                cv2.line(output, pt_a, pt_b, color, 1)

        cv2.imwrite(output_path, output)

        evidence = []
        if suspicious:
            evidence.append("Localized repeated feature pattern consistent with copy-move duplication")

        return {
            "success": True,
            "keypoints": int(len(keypoints)),
            "matches": int(len(candidates)),
            "inliers": int(len(best_inliers)),
            "inlier_ratio": round(float(best_ratio), 3),
            "displacement": round(float(best_disp), 2),
            "suspicious": suspicious,
            "evidence": evidence,
            "output": output_path
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
