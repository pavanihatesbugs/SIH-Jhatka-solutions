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

# NEW FORENSIC MODULES
from .resampling import analyze_resampling
from .edge_analysis import analyze_edges
from .jpeg_analysis import analyze_jpeg

# RISK ENGINE
from .risk_score import calculate_forensic_score


def analyze_forensics(file_path):
    """
    Main forensic analysis pipeline.

    Supports:
        JPG
        JPEG
        PNG
        PDF

    Returns a JSON-compatible dictionary.
    """

    # ======================================================
    # VALIDATE INPUT
    # ======================================================

    if not file_path:

        return {
            "success": False,
            "message": "No file path provided"
        }

    if not os.path.exists(file_path):

        return {
            "success": False,
            "message": "File not found",
            "file": file_path
        }

    extension = (
        os.path.splitext(
            file_path
        )[1]
        .lower()
    )

    # ======================================================
    # STEP 1
    # HANDLE INPUT
    # ======================================================

    if extension == ".pdf":

        try:

            image_paths = (
                convert_pdf_to_images(
                    file_path
                )
            )

        except Exception as e:

            return {
                "success": False,
                "message":
                    f"PDF conversion failed: {str(e)}",
                "file":
                    file_path
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

            "success":
                False,

            "message":
                "Unsupported file format",

            "file":
                file_path
        }

    # ======================================================
    # STEP 2
    # ANALYZE EACH PAGE
    # ======================================================

    results = []

    for image_path in image_paths:

        # ==================================================
        # LOAD IMAGE
        # ==================================================

        image = load_image(
            image_path
        )

        if image is None:

            continue

        # ==================================================
        # IMAGE QUALITY
        # ==================================================

        try:

            quality = check_image_quality(
                image_path
            )

        except Exception as e:

            quality = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # ELA
        # ==================================================

        ela_output = os.path.join(

            "working",

            "ela_" +
            os.path.basename(
                image_path
            )
        )

        try:

            ela = perform_ela(
                image_path,
                ela_output
            )

        except Exception as e:

            ela = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # METADATA
        # ==================================================

        try:

            metadata = analyze_image_metadata(
                image_path
            )

        except Exception as e:

            metadata = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # NOISE
        # ==================================================

        noise_output = os.path.join(

            "working",

            "noise_" +
            os.path.basename(
                image_path
            )
        )

        try:

            noise = analyze_noise(
                image_path,
                noise_output
            )

        except Exception as e:

            noise = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # COPY-MOVE
        # ==================================================

        copy_move_output = os.path.join(

            "working",

            "copy_move_" +
            os.path.basename(
                image_path
            )
        )

        try:

            copy_move = detect_copy_move(
                image_path,
                copy_move_output
            )

        except Exception as e:

            copy_move = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # RESAMPLING
        # ==================================================

        try:

            resampling = analyze_resampling(
                image_path
            )

        except Exception as e:

            resampling = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # EDGE ANALYSIS
        # ==================================================

        try:

            edge_analysis = analyze_edges(
                image_path
            )

        except Exception as e:

            edge_analysis = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # JPEG ANALYSIS
        # ==================================================

        try:

            jpeg_analysis = analyze_jpeg(
                image_path
            )

        except Exception as e:

            jpeg_analysis = {

                "success":
                    False,

                "error":
                    str(e)
            }

        # ==================================================
        # COMBINE PAGE RESULTS
        # ==================================================

        page_result = {

            "image":
                image_path,

            "quality":
                quality,

            "ela":
                ela,

            "metadata":
                metadata,

            "noise":
                noise,

            "copy_move":
                copy_move,

            "resampling":
                resampling,

            "edge_analysis":
                edge_analysis,

            "jpeg_analysis":
                jpeg_analysis
        }

        # ==================================================
        # EVIDENCE FUSION
        # ==================================================

        try:

            forensic_score = (
                calculate_forensic_score(
                    page_result
                )
            )

        except Exception as e:

            forensic_score = {

                "forensic_score":
                    0,

                "risk_level":
                    "LOW",

                "confidence":
                    0.0,

                "evidence": [
                    "Risk calculation failed"
                ],

                "error":
                    str(e)
            }

        # Add final score to page
        page_result[
            "forensic_score"
        ] = forensic_score

        # ==================================================
        # APPEND
        # ==================================================

        results.append(
            page_result
        )

    # ======================================================
    # STEP 3
    # DOCUMENT-LEVEL SCORE
    # ======================================================

    if results:

        page_scores = [

            page[
                "forensic_score"
            ][
                "forensic_score"
            ]

            for page in results

            if isinstance(
                page.get(
                    "forensic_score"
                ),
                dict
            )
        ]

        if page_scores:

            document_score = max(
                page_scores
            )

        else:

            document_score = 0

    else:

        document_score = 0

    # ======================================================
    # DOCUMENT RISK
    # ======================================================

    if document_score >= 60:

        document_risk = "HIGH"

    elif document_score >= 30:

        document_risk = "MEDIUM"

    else:

        document_risk = "LOW"

    # ======================================================
    # FINAL DOCUMENT RESPONSE
    # ======================================================

    return {

        "success":
            True,

        "file":
            file_path,

        "pages_analyzed":
            len(results),

        "document_forensic_score":
            document_score,

        "document_risk_level":
            document_risk,

        "results":
            results
    }