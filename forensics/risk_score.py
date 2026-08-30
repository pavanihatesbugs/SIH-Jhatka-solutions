"""
Forensic Evidence Fusion Engine.

Combines independent forensic signals into a coherent risk evaluation.
The forensic score provides an evidence/risk estimation and is not a
definitive legal determination of fraud.
"""

WEIGHTS = {
    "ela": 0.28,
    "copy_move": 0.25,
    "edge": 0.15,
    "jpeg": 0.12,
    "noise": 0.10,
    "resampling": 0.08,
    "metadata": 0.02,
}


def clamp(value, minimum=0.0, maximum=100.0):
    try:
        val = float(value)
    except (TypeError, ValueError):
        val = 0.0
    return max(minimum, min(val, maximum))


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_ela_signal(ela):
    if not isinstance(ela, dict) or not ela.get("success", False):
        return 0.0

    score = _num(ela.get("max_local_score", 0))
    suspicious_regions = int(_num(ela.get("suspicious_regions", 0)))
    covering = bool(ela.get("covering_suspicious", False))
    localized = bool(ela.get("localized_suspicious", False))

    if not localized and suspicious_regions == 0:
        return 0.0

    signal = 0.0
    if localized:
        signal = max(signal, 50.0)

    if score >= 75:
        signal += 35.0
    elif score >= 55:
        signal += 25.0
    elif score >= 40:
        signal += 15.0

    if suspicious_regions >= 2:
        signal += 15.0
    elif suspicious_regions >= 1:
        signal += 8.0

    if covering:
        signal += 10.0

    return clamp(signal)


def calculate_noise_signal(noise):
    if not isinstance(noise, dict) or not noise.get("success", False):
        return 0.0

    if not noise.get("suspicious", False):
        return 0.0

    inconsistency = _num(noise.get("noise_inconsistency", 0))
    score = _num(noise.get("noise_score", 0))

    signal = 0.0
    if inconsistency >= 20.0 and score >= 5.0:
        signal = 80.0
    elif inconsistency >= 15.0 and score >= 4.0:
        signal = 60.0
    elif inconsistency >= 10.0:
        signal = 40.0

    return clamp(signal)


def calculate_copy_move_signal(copy_move):
    if not isinstance(copy_move, dict) or not copy_move.get("success", False):
        return 0.0
    if not copy_move.get("suspicious", False):
        return 0.0

    inliers = int(_num(copy_move.get("inliers", 0)))
    ratio = _num(copy_move.get("inlier_ratio", 0))

    if inliers >= 15 and ratio >= 0.60:
        return 100.0
    if inliers >= 10 and ratio >= 0.50:
        return 85.0
    if inliers >= 6 and ratio >= 0.45:
        return 70.0
    return 50.0


def calculate_resampling_signal(resampling):
    if not isinstance(resampling, dict) or not resampling.get("success", False):
        return 0.0

    score = clamp(resampling.get("resampling_score", 0))
    if score < 40.0:
        return 0.0

    return score


def calculate_edge_signal(edge):
    if not isinstance(edge, dict) or not edge.get("success", False):
        return 0.0

    if not edge.get("suspicious", False):
        return 0.0

    max_edge = clamp(edge.get("max_edge_score", 0))
    high_regions = int(_num(edge.get("high_confidence_regions", 0)))

    if high_regions <= 0:
        return 0.0

    return max_edge


def calculate_jpeg_signal(jpeg):
    if not isinstance(jpeg, dict) or not jpeg.get("success", False):
        return 0.0

    if not jpeg.get("suspicious", False):
        return 0.0

    score = clamp(jpeg.get("jpeg_score", 0))
    return score


def calculate_metadata_signal(metadata):
    if not isinstance(metadata, dict) or not metadata.get("success", False):
        return 0.0

    # Missing EXIF is normal for web uploads, scans, and screenshots.
    return 0.0


def calculate_quality_confidence(quality):
    if not isinstance(quality, dict) or not quality.get("success", False):
        return {
            "confidence": 0.75,
            "evidence": ["Image quality could not be evaluated"]
        }

    blur = _num(quality.get("blur_score", 0))
    brightness = _num(quality.get("brightness", 128))

    confidence = 1.0
    evidence = []

    if blur < 40:
        confidence -= 0.25
        evidence.append("Severe image blur reduces forensic confidence")
    elif blur < 80:
        confidence -= 0.10
        evidence.append("Moderate blur reduces forensic confidence")

    if brightness < 20 or brightness > 245:
        confidence -= 0.15
        evidence.append("Extreme brightness levels may impact forensic analysis")

    return {
        "confidence": max(0.50, min(1.0, confidence)),
        "evidence": evidence
    }


def calculate_forensic_score(result):
    """
    Combine independent forensic detector outputs into a single overall score.

    Returns:
        {
            "forensic_score": 0-100,
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "confidence": 0.0-1.0,
            "signal_breakdown": {...},
            "active_signals": [...],
            "agreement_bonus": int,
            "evidence": [...]
        }
    """
    if not isinstance(result, dict):
        return {
            "forensic_score": 0,
            "risk_level": "LOW",
            "confidence": 0.0,
            "signal_breakdown": {},
            "active_signals": [],
            "agreement_bonus": 0,
            "evidence": ["Invalid forensic input"]
        }

    signals = {
        "ela": calculate_ela_signal(result.get("ela", {})),
        "noise": calculate_noise_signal(result.get("noise", {})),
        "copy_move": calculate_copy_move_signal(result.get("copy_move", {})),
        "resampling": calculate_resampling_signal(result.get("resampling", {})),
        "edge": calculate_edge_signal(result.get("edge_analysis", {})),
        "jpeg": calculate_jpeg_signal(result.get("jpeg_analysis", {})),
        "metadata": calculate_metadata_signal(result.get("metadata", {})),
    }

    active = []
    evidence = []

    if signals["ela"] >= 45.0:
        active.append("ELA")
        evidence.append("Localized Error Level Analysis (ELA) anomaly detected")
    elif signals["ela"] >= 30.0:
        active.append("ELA")
        evidence.append("Moderate ELA compression inconsistency detected")

    if signals["noise"] >= 40.0:
        active.append("NOISE")
        evidence.append("Localized noise variance inconsistency detected")

    if signals["copy_move"] >= 50.0:
        active.append("COPY_MOVE")
        evidence.append("Geometrically consistent copy-move feature duplication detected")

    if signals["resampling"] >= 45.0:
        active.append("RESAMPLING")
        evidence.append("Periodic resampling/interpolation spectral artifact detected")

    if signals["edge"] >= 55.0:
        active.append("EDGE")
        evidence.append("Localized suspicious internal boundary anomaly detected")

    if signals["jpeg"] >= 50.0:
        active.append("JPEG")
        evidence.append("Localized JPEG DCT block-level inconsistency detected")

    quality_info = calculate_quality_confidence(result.get("quality", {}))
    confidence = float(quality_info["confidence"])

    weighted_score = sum(signals[name] * WEIGHTS[name] for name in signals)

    strong_signals = [name for name, val in signals.items() if name != "metadata" and val >= 65.0]
    moderate_signals = [name for name, val in signals.items() if name != "metadata" and val >= 35.0]

    agreement_bonus = 0
    if len(moderate_signals) >= 4:
        agreement_bonus = 18
    elif len(moderate_signals) >= 3:
        agreement_bonus = 12
    elif len(moderate_signals) >= 2:
        agreement_bonus = 8

    if len(strong_signals) >= 3:
        agreement_bonus += 15
    elif len(strong_signals) >= 2:
        agreement_bonus += 10

    # Rule: a single weak/supporting signal (e.g. edge alone, noise alone, jpeg alone, resampling alone)
    # is deliberately capped at LOW risk to prevent normal document structures from raising alarms.
    nonzero_signals = [name for name, val in signals.items() if val > 0.0 and name != "metadata"]

    if len(nonzero_signals) == 1 and nonzero_signals[0] in {"edge", "jpeg", "noise", "resampling"}:
        weighted_score = min(weighted_score, 18.0)
        agreement_bonus = 0

    raw_score = weighted_score + agreement_bonus

    # Standalone strong detector support (e.g. unambiguous copy-move or strong ELA)
    if len(nonzero_signals) == 1:
        only = nonzero_signals[0]
        if only == "copy_move" and signals[only] >= 85.0:
            raw_score = max(raw_score, 65.0)
        elif only == "ela" and signals[only] >= 80.0:
            raw_score = max(raw_score, 55.0)

    adjusted_score = raw_score * (0.75 + 0.25 * confidence)
    final_score = int(round(clamp(adjusted_score)))

    evidence.extend(quality_info["evidence"])

    metadata_dict = result.get("metadata", {}).get("metadata", {})
    if not metadata_dict:
        evidence.append("No useful EXIF metadata available (normal for scans/screenshots)")

    if final_score >= 60:
        risk_level = "HIGH"
    elif final_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if not active:
        evidence.append("No significant forensic manipulation detected")
    elif len(nonzero_signals) == 1 and final_score < 30:
        evidence.append("Isolated supporting signal without corroborating anomalies")

    return {
        "forensic_score": final_score,
        "risk_level": risk_level,
        "confidence": round(confidence, 2),
        "signal_breakdown": {k: round(v, 2) for k, v in signals.items()},
        "active_signals": active,
        "agreement_bonus": int(agreement_bonus),
        "evidence": evidence
    }
