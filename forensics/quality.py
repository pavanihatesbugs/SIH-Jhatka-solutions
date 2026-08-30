import cv2


def check_image_quality(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "message": "Could not read image"
        }

    # Get image dimensions
    height, width = image.shape[:2]

    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate blur score
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Calculate average brightness
    brightness = float(gray.mean())

    return {
        "success": True,
        "width": int(width),
        "height": int(height),
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2)
    }