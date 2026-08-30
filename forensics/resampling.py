import os
import cv2
import numpy as np


def analyze_resampling(image_path, output_dir="working"):
    """
    Analyze periodic interpolation and resampling artifacts.

    Resampling operations (scaling, rotation, affine transformations) leave
    subtle periodic correlation in the spatial derivative / gradient spectrum.
    This module inspects spectral energy concentration via 2D FFT.

    Returns a JSON-compatible dictionary.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return {"success": False, "error": "Unable to read image"}

        height, width = image.shape
        if height < 50 or width < 50:
            return {"success": False, "error": "Image too small for resampling analysis"}

        # Calculate second derivative / Laplacian for subtle interpolation correlation
        gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        gradient = np.sqrt(gx * gx + gy * gy)

        # Normalize gradient
        g_min = float(gradient.min())
        g_max = float(gradient.max())
        if g_max - g_min > 1e-6:
            gradient = (gradient - g_min) / (g_max - g_min)

        # 2D Fourier transform of gradient
        fft = np.fft.fft2(gradient)
        fft_shifted = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shifted)
        magnitude = np.log1p(magnitude)

        # Mask out central DC and low-frequency components
        cy = height // 2
        cx = width // 2
        radius = max(5, min(height, width) // 30)

        yy, xx = np.ogrid[:height, :width]
        center_mask = ((yy - cy) ** 2 + (xx - cx) ** 2) <= (radius ** 2)
        magnitude[center_mask] = 0.0

        # Calculate spectral peak concentration
        total_energy = float(np.sum(magnitude))
        if total_energy <= 0:
            periodicity = 0.0
            score = 0.0
        else:
            flat = magnitude.flatten()
            k = min(100, len(flat))
            top_values = np.partition(flat, -k)[-k:]
            peak_energy = float(np.sum(top_values))
            periodicity = peak_energy / total_energy

            # Scale periodicity into standard 0-100 score:
            # Baseline natural images have periodicity ~0.0001 - 0.0004
            # Resampled images have periodicity ~0.0008 - 0.0025+
            raw_score = (periodicity - 0.0002) / 0.0012 * 80.0
            score = float(max(0.0, min(100.0, raw_score)))

        # Visual spectral output
        spectral_output = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        filename = os.path.basename(image_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"resampling_{name}.png")
        cv2.imwrite(output_path, spectral_output)

        suspicious = bool(score >= 45.0)
        evidence = []
        if score >= 60.0:
            evidence.append("Strong resampling/interpolation spectral pattern detected")
        elif score >= 40.0:
            evidence.append("Possible resampling/interpolation artifact detected")

        return {
            "success": True,
            "resampling_score": round(score, 2),
            "periodicity": round(float(periodicity), 6),
            "suspicious": suspicious,
            "evidence": evidence,
            "output": output_path
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
