import os

from .quality import check_image_quality
from .ela import perform_ela
from .input_handler import (
    load_image,
    convert_pdf_to_images
)
from .metadata import analyze_image_metadata
from .noise import analyze_noise
from .copy_move import detect_copy_move
from .risk_score import calculate_forensic_score


def analyze_forensics(file_path):
    """
    Main forensic analysis function.

    Accepts:
        PDF
        JPG
        JPEG
        PNG

    The file path is provided by the caller.

    Returns a dictionary containing:
        - document-level forensic score
        - document risk level
        - document confidence
        - evidence
        - page-level forensic results
    """

    # ============================================================
    # STEP 1: CHECK WHETHER FILE EXISTS
    # ============================================================

    if not os.path.exists(file_path):

        return {
            "success": False,
            "file": file_path,
            "message": "File does not exist"
        }

    # ============================================================
    # STEP 2: GET FILE EXTENSION
    # ============================================================

    extension = os.path.splitext(
        file_path
    )[1].lower()

    # ============================================================
    # STEP 3: HANDLE INPUT FILE
    # ============================================================

    if extension == ".pdf":

        try:

            image_paths = convert_pdf_to_images(
                file_path
            )

        except Exception as error:

            return {
                "success": False,
                "file": file_path,
                "message": "PDF conversion failed",
                "error": str(error)
            }

    elif extension in [
        ".jpg",
        ".jpeg",
        ".png"
    ]:

        image_paths = [
            file_path
        ]

    else:

        return {
            "success": False,
            "file": file_path,
            "message": "Unsupported file format"
        }

    # ============================================================
    # STEP 4: CHECK WHETHER IMAGES WERE CREATED
    # ============================================================

    if not image_paths:

        return {
            "success": False,
            "file": file_path,
            "message": "No images/pages found"
        }

    # ============================================================
    # STEP 5: CREATE WORKING DIRECTORY
    # ============================================================

    os.makedirs(
        "working",
        exist_ok=True
    )

    # ============================================================
    # STEP 6: ANALYZE EACH IMAGE/PDF PAGE
    # ============================================================

    results = []

    for image_path in image_paths:

        # ========================================================
        # LOAD IMAGE
        # ========================================================

        image = load_image(
            image_path
        )

        if image is None:

            continue

        # ========================================================
        # IMAGE QUALITY
        # ========================================================

        quality = check_image_quality(
            image_path
        )

        # ========================================================
        # ELA
        # ========================================================

        ela_output = os.path.join(
            "working",
            "ela_" +
            os.path.basename(
                image_path
            )
        )

        ela = perform_ela(
            image_path,
            ela_output
        )

        # ========================================================
        # METADATA
        # ========================================================

        metadata = analyze_image_metadata(
            image_path
        )

        # ========================================================
        # NOISE
        # ========================================================

        noise_output = os.path.join(
            "working",
            "noise_" +
            os.path.basename(
                image_path
            )
        )

        noise = analyze_noise(
            image_path,
            noise_output
        )

        # ========================================================
        # COPY-MOVE
        # ========================================================

        copy_move_output = os.path.join(
            "working",
            "copy_move_" +
            os.path.basename(
                image_path
            )
        )

        copy_move = detect_copy_move(
            image_path,
            copy_move_output
        )

        # ========================================================
        # CREATE PAGE RESULT
        # ========================================================

        page_result = {

            "image": image_path,

            "quality": quality,

            "ela": ela,

            "metadata": metadata,

            "noise": noise,

            "copy_move": copy_move
        }

        # ========================================================
        # CALCULATE PAGE FORENSIC SCORE
        # ========================================================

        forensic_score = calculate_forensic_score(
            page_result
        )

        page_result[
            "forensic_score"
        ] = forensic_score

        # ========================================================
        # SAVE PAGE RESULT
        # ========================================================

        results.append(
            page_result
        )

    # ============================================================
    # STEP 7: CHECK ANALYSIS RESULT
    # ============================================================

    if not results:

        return {
            "success": False,
            "file": file_path,
            "message": "No pages could be analyzed"
        }

    # ============================================================
    # STEP 8: GET PAGE FORENSIC SCORES
    # ============================================================

    page_scores = []

    for page in results:

        score_data = page.get(
            "forensic_score",
            {}
        )

        page_score = score_data.get(
            "forensic_score",
            0
        )

        page_scores.append(
            page_score
        )

    # ============================================================
    # STEP 9: CALCULATE DOCUMENT SCORE
    # ============================================================
    #
    # For a multi-page PDF, use the highest page score.
    #
    # Example:
    #
    # Page 1 = 10
    # Page 2 = 15
    # Page 3 = 65
    #
    # Document score = 65
    #
    # ============================================================

    document_score = max(
        page_scores
    )

    # ============================================================
    # STEP 10: DOCUMENT RISK LEVEL
    # ============================================================

    if document_score < 30:

        document_risk = "LOW"

    elif document_score < 60:

        document_risk = "MEDIUM"

    else:

        document_risk = "HIGH"

    # ============================================================
    # STEP 11: COLLECT DOCUMENT EVIDENCE
    # ============================================================

    document_evidence = []

    for page in results:

        score_data = page.get(
            "forensic_score",
            {}
        )

        page_evidence = score_data.get(
            "evidence",
            []
        )

        for evidence in page_evidence:

            if evidence not in document_evidence:

                document_evidence.append(
                    evidence
                )

    # ============================================================
    # STEP 12: DOCUMENT CONFIDENCE
    # ============================================================

    page_confidences = []

    for page in results:

        score_data = page.get(
            "forensic_score",
            {}
        )

        confidence = score_data.get(
            "confidence",
            1.0
        )

        page_confidences.append(
            confidence
        )

    if page_confidences:

        document_confidence = min(
            page_confidences
        )

    else:

        document_confidence = 1.0

    # ============================================================
    # STEP 13: FINAL RESULT
    # ============================================================

    return {

        "success": True,

        "file": file_path,

        "pages_analyzed": len(
            results
        ),

        "document_forensic_score":
            document_score,

        "document_risk_level":
            document_risk,

        "document_confidence":
            round(
                document_confidence,
                2
            ),

        "evidence":
            document_evidence,

        "results":
            results
    }