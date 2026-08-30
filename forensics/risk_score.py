def calculate_forensic_score(result):
    """
    Calculate forensic anomaly score for one image/page.

    Score:
        0   - 100

    This score represents forensic evidence/anomalies.
    It should be passed to the larger project risk engine.

    It does NOT by itself prove that a document is fraudulent.
    """

    score = 0

    evidence = []

    # ============================================================
    # ELA
    # ============================================================

    ela = result.get(
        "ela",
        {}
    )

    if ela.get("success"):

        global_ela = ela.get(
            "score",
            0
        )

        localized_ela = ela.get(
            "localized_suspicious",
            False
        )

        suspicious_regions = ela.get(
            "suspicious_regions",
            0
        )

        max_local_ela = ela.get(
            "max_local_score",
            0
        )

        # --------------------------------------------------------
        # GLOBAL ELA
        # --------------------------------------------------------

        if global_ela > 10:

            score += 20

            evidence.append(
                "High global ELA anomaly detected"
            )

        elif global_ela > 5:

            score += 10

            evidence.append(
                "Moderate global ELA anomaly detected"
            )

        # --------------------------------------------------------
        # LOCALIZED ELA
        # --------------------------------------------------------

        if localized_ela:

            score += 25

            evidence.append(
                "Localized ELA anomaly detected"
            )

        elif max_local_ela > 8:

            score += 15

            evidence.append(
                "Strong local ELA variation detected"
            )

        # --------------------------------------------------------
        # MULTIPLE ELA REGIONS
        # --------------------------------------------------------

        if suspicious_regions >= 3:

            score += 5

            evidence.append(
                "Multiple localized ELA regions detected"
            )

        # --------------------------------------------------------
        # COVERING-LIKE REGIONS
        # --------------------------------------------------------

        covering_suspicious = ela.get(
            "covering_suspicious",
            False
        )

        covering_regions = ela.get(
            "covering_regions",
            0
        )

        max_covering_score = ela.get(
            "max_covering_score",
            0
        )

        # Strong covering-like region.

        if covering_suspicious:

            if max_covering_score >= 75:

                score += 25

                evidence.append(
                    "Strong localized covering-like region detected"
                )

            elif max_covering_score >= 50:

                score += 20

                evidence.append(
                    "Localized covering-like region detected"
                )

            else:

                score += 10

                evidence.append(
                    "Possible localized surface alteration detected"
                )

        # Multiple covering regions.

        if covering_regions >= 2:

            score += 10

            evidence.append(
                "Multiple covering-like regions detected"
            )

    # ============================================================
    # NOISE
    # ============================================================

    noise = result.get(
        "noise",
        {}
    )

    if noise.get("success"):

        noise_score = noise.get(
            "noise_score",
            0
        )

        if noise_score > 10:

            score += 20

            evidence.append(
                "High noise inconsistency detected"
            )

        elif noise_score > 5:

            score += 10

            evidence.append(
                "Moderate noise inconsistency detected"
            )

    # ============================================================
    # COPY-MOVE
    # ============================================================

    copy_move = result.get(
        "copy_move",
        {}
    )

    if copy_move.get("success"):

        if copy_move.get(
            "suspicious",
            False
        ):

            score += 30

            evidence.append(
                "Possible copy-move manipulation detected"
            )

    # ============================================================
    # METADATA
    # ============================================================

    metadata = result.get(
        "metadata",
        {}
    )

    if metadata.get("success"):

        metadata_info = metadata.get(
            "metadata",
            {}
        )

        # Missing metadata is NOT treated as fraud.

        if not metadata_info:

            evidence.append(
                "No useful metadata available"
            )

    # ============================================================
    # IMAGE QUALITY / CONFIDENCE
    # ============================================================

    quality = result.get(
        "quality",
        {}
    )

    confidence = 1.0

    if quality.get("success"):

        blur_score = quality.get(
            "blur_score",
            0
        )

        brightness = quality.get(
            "brightness",
            0
        )

        # --------------------------------------------------------
        # BLUR
        # --------------------------------------------------------

        if blur_score < 100:

            confidence -= 0.20

            evidence.append(
                "Low image quality may reduce forensic confidence"
            )

        # --------------------------------------------------------
        # BRIGHTNESS
        # --------------------------------------------------------

        if (
            brightness < 30
            or
            brightness > 230
        ):

            confidence -= 0.10

            evidence.append(
                "Unusual image brightness"
            )

    # ============================================================
    # LIMIT SCORE
    # ============================================================

    score = min(
        max(score, 0),
        100
    )

    confidence = min(
        max(confidence, 0),
        1
    )

    # ============================================================
    # RISK LEVEL
    # ============================================================

    if score < 30:

        risk_level = "LOW"

    elif score < 60:

        risk_level = "MEDIUM"

    else:

        risk_level = "HIGH"

    # ============================================================
    # RETURN
    # ============================================================

    return {

        "forensic_score":
            score,

        "risk_level":
            risk_level,

        "confidence":
            round(
                confidence,
                2
            ),

        "evidence":
            evidence
    }