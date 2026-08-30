import cv2
import numpy as np


def perform_ela(image_path, output_path="ela_result.jpg"):

    # Read original image
    original = cv2.imread(image_path)

    if original is None:
        return {
            "success": False,
            "message": "Could not read image"
        }

    # Save a JPEG-compressed copy
    temporary_file = "temporary_compressed.jpg"

    cv2.imwrite(
        temporary_file,
        original,
        [cv2.IMWRITE_JPEG_QUALITY, 90]
    )

    # Read compressed image
    compressed = cv2.imread(temporary_file)

    if compressed is None:
        return {
            "success": False,
            "message": "Could not read compressed image"
        }

    # Calculate pixel differences
    difference = cv2.absdiff(original, compressed)

    # Convert difference to grayscale
    difference_gray = cv2.cvtColor(
        difference,
        cv2.COLOR_BGR2GRAY
    )

    # Normalize differences to full 0-255 range
    ela_image = cv2.normalize(
        difference_gray,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    # Save ELA image
    cv2.imwrite(output_path, ela_image)

    # Calculate average error
    ela_score = float(np.mean(ela_image))

    return {
        "success": True,
        "score": ela_score,
        "output": output_path
    }