import os

from .quality import check_image_quality
from .ela import perform_ela
from .input_handler import load_image, convert_pdf_to_images
from .metadata import analyze_image_metadata
from .noise import analyze_noise
from .copy_move import detect_copy_move
from .risk_score import calculate_forensic_score


def analyze_forensics(file_path):

    # ============================================================
    # STEP 1: CHECK INPUT
    # ============================================================

    if not os.path.exists(file_path):

        return {
            "success": False,
            "message": "File not found",
            "file": file_path
        }


    extension = os.path.splitext(file_path)[1].lower()


    # ============================================================
    # STEP 2: HANDLE INPUT FILE
    # ============================================================

    if extension == ".pdf":

        image_paths = convert_pdf_to_images(
            file_path
        )

    elif extension in [".jpg", ".jpeg", ".png"]:

        image_paths = [
            file_path
        ]

    else:

        return {
            "success": False,
            "message": "Unsupported file format",
            "file": file_path
        }


    # ============================================================
    # STEP 3: CHECK WHETHER IMAGES WERE CREATED
    # ============================================================

    if not image_paths:

        return {
            "success": False,
            "message": "Could not extract any pages/images",
            "file": file_path
        }


    # ============================================================
    # STEP 4: ANALYZE EACH PAGE
    # ============================================================

    results = []


    for image_path in image_paths:

        print(
            "\nAnalyzing:",
            image_path
        )


        # --------------------------------------------------------
        # Make sure image can be opened
        # --------------------------------------------------------

        image = load_image(
            image_path
        )


        if image is None:

            print(
                "Could not open:",
                image_path
            )

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

        ela_output = (
            "ela_" +
            os.path.basename(image_path)
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

        noise_output = (
            "noise_" +
            os.path.basename(image_path)
        )


        noise = analyze_noise(
            image_path,
            noise_output
        )


        # ========================================================
        # COPY-MOVE
        # ========================================================

        copy_move_output = (
            "copy_move_" +
            os.path.basename(image_path)
        )


        copy_move = detect_copy_move(
            image_path,
            copy_move_output
        )


        # ========================================================
        # STORE RAW FORENSIC RESULTS
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
        # STEP 5: CALCULATE PAGE FORENSIC SCORE
        # ========================================================

        forensic_score = calculate_forensic_score(
            page_result
        )


        page_result[
            "forensic_score"
        ] = forensic_score


        # ========================================================
        # ADD PAGE RESULT
        # ========================================================

        results.append(
            page_result
        )


    # ============================================================
    # STEP 6: CHECK WHETHER ANY PAGE WAS SUCCESSFULLY ANALYZED
    # ============================================================

    if not results:

        return {
            "success": False,
            "message": "No pages could be analyzed",
            "file": file_path,
            "pages_analyzed": 0,
            "results": []
        }


    # ============================================================
    # STEP 7: DOCUMENT-LEVEL SCORE
    # ============================================================
    #
    # For a multi-page PDF:
    #
    # Page 1 → 10
    # Page 2 → 65
    # Page 3 → 20
    #
    # Document score = 65
    #
    # We use the highest page score because a suspicious
    # page should not be hidden by averaging it with clean pages.
    # ============================================================

    page_scores = [

        page["forensic_score"]["forensic_score"]

        for page in results

        if "forensic_score" in page
    ]


    if page_scores:

        document_score = max(
            page_scores
        )

    else:

        document_score = 0


    # ============================================================
    # STEP 8: DOCUMENT RISK LEVEL
    # ============================================================

    if document_score < 30:

        document_risk_level = "LOW"

    elif document_score < 60:

        document_risk_level = "MEDIUM"

    else:

        document_risk_level = "HIGH"


    # ============================================================
    # STEP 9: GET MOST IMPORTANT EVIDENCE
    # ============================================================

    evidence = []


    for page in results:

        page_score = page.get(
            "forensic_score",
            {}
        )


        page_evidence = page_score.get(
            "evidence",
            []
        )


        for item in page_evidence:

            if item not in evidence:

                evidence.append(
                    item
                )


    # ============================================================
    # STEP 10: FINAL RESULT
    # ============================================================

    return {

        "success": True,

        "file": file_path,

        "pages_analyzed": len(results),

        "document_forensic_score": document_score,

        "document_risk_level": document_risk_level,

        "evidence": evidence,

        "results": results
    }