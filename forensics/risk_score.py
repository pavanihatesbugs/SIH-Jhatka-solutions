def calculate_forensic_score(result):

    score = 0
    evidence = []

    # ============================================
    # ELA
    # ============================================

    ela = result.get("ela", {})

    if ela.get("success"):

        ela_score = ela.get("score", 0)

        if ela_score > 10:
            score += 25
            evidence.append(
                "High ELA anomaly detected"
            )

        elif ela_score > 5:
            score += 15
            evidence.append(
                "Moderate ELA anomaly detected"
            )

        else:
            score += 0


    # ============================================
    # NOISE
    # ============================================

    noise = result.get("noise", {})

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


    # ============================================
    # COPY-MOVE
    # ============================================

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


    # ============================================
    # METADATA
    # ============================================

    metadata = result.get(
        "metadata",
        {}
    )

    if metadata.get("success"):

        metadata_info = metadata.get(
            "metadata",
            {}
        )

        # For now, missing metadata is NOT automatically fraud.
        # We only record it as evidence.

        if not metadata_info:

            evidence.append(
                "No useful metadata available"
            )


    # ============================================
    # QUALITY
    # ============================================

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

        # Poor image quality reduces confidence.
        if blur_score < 100:

            confidence -= 0.20

            evidence.append(
                "Low image quality may reduce forensic confidence"
            )

        if brightness < 30 or brightness > 230:

            confidence -= 0.10

            evidence.append(
                "Unusual image brightness"
            )


    # ============================================
    # LIMIT SCORE
    # ============================================

    score = min(
        max(score, 0),
        100
    )

    confidence = min(
        max(confidence, 0),
        1
    )


    # ============================================
    # RISK LEVEL
    # ============================================

    if score < 30:

        risk_level = "LOW"

    elif score < 60:

        risk_level = "MEDIUM"

    else:

        risk_level = "HIGH"


    # ============================================
    # FINAL RESULT
    # ============================================

    return {

        "forensic_score": score,

        "risk_level": risk_level,

        "confidence": round(
            confidence,
            2
        ),

        "evidence": evidence
    }