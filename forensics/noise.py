import cv2
import numpy as np


def analyze_noise(image_path, output_path="noise_result.png"):

    # Read image
    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "message": "Could not read image"
        }

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur the image to estimate the underlying smooth image
    smooth = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # Calculate noise residual
    noise = cv2.absdiff(gray, smooth)

    # Increase visibility
    noise_map = cv2.normalize(
        noise,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    # Save noise visualization
    cv2.imwrite(output_path, noise_map)

    # Calculate average noise
    noise_score = float(np.mean(noise))

    return {
        "success": True,
        "noise_score": noise_score,
        "output": output_path
    }