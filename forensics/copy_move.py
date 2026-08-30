import cv2
import numpy as np


def detect_copy_move(
    image_path,
    output_path="copy_move_result.png"
):

    # Read image
    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "message": "Could not read image"
        }

    # Convert to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Create ORB detector
    orb = cv2.ORB_create(
        nfeatures=1000
    )

    # Find keypoints and descriptors
    keypoints, descriptors = orb.detectAndCompute(
        gray,
        None
    )

    # Not enough features
    if descriptors is None or len(keypoints) < 2:

        return {
            "success": True,
            "matches": 0,
            "suspicious": False,
            "output": output_path
        }

    # Create feature matcher
    matcher = cv2.BFMatcher(
        cv2.NORM_HAMMING,
        crossCheck=True
    )

    # Match descriptors with themselves
    matches = matcher.match(
        descriptors,
        descriptors
    )

    # Remove self-matches
    matches = [
        match for match in matches
        if match.queryIdx != match.trainIdx
    ]

    # Sort matches by quality
    matches = sorted(
        matches,
        key=lambda x: x.distance
    )

    # Keep strong matches
    good_matches = [
        match for match in matches
        if match.distance < 30
    ]

    # Create result image
    result = image.copy()

    suspicious_points = []

    for match in good_matches:

        point1 = keypoints[match.queryIdx].pt
        point2 = keypoints[match.trainIdx].pt

        distance = np.linalg.norm(
            np.array(point1) - np.array(point2)
        )

        # Ignore matches that are extremely close
        if distance > 30:

            suspicious_points.append(
                (int(point1[0]), int(point1[1]))
            )

            suspicious_points.append(
                (int(point2[0]), int(point2[1]))
            )

            cv2.circle(
                result,
                (int(point1[0]), int(point1[1])),
                8,
                (255, 255, 255),
                2
            )

            cv2.circle(
                result,
                (int(point2[0]), int(point2[1])),
                8,
                (255, 255, 255),
                2
            )

    # Save visualization
    cv2.imwrite(
        output_path,
        result
    )

    # Determine whether suspicious matches exist
    suspicious = len(suspicious_points) >= 4

    return {
        "success": True,
        "keypoints": len(keypoints),
        "matches": len(good_matches),
        "suspicious_points": len(suspicious_points),
        "suspicious": suspicious,
        "output": output_path
    }