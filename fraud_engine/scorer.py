def calculate_pan_score(matches, forensic_data):

    score = 0
    reasons = []

    

    if matches["name_similarity"] < 0.85:
        score += 25
        reasons.append(
            "Name does not sufficiently match database"
        )

    if matches["father_similarity"] < 0.85:
        score += 20
        reasons.append(
            "Father's name does not sufficiently match database"
        )

    if not matches["dob_match"]:
        score += 20
        reasons.append(
            "Date of birth does not match database"
        )

    score, reasons = add_forensic_score(
        score,
        reasons,
        forensic_data
    )

   

    return finalize_score(score, reasons)


def calculate_aadhaar_score(matches, forensic_data):

    score = 0
    reasons = []

    if not matches["aadhaar_match"]:
        score += 40
        reasons.append(
            "Aadhaar number does not match database"
        )

    if matches["name_similarity"] < 0.85:
        score += 20
        reasons.append(
            "Name does not sufficiently match database"
        )

    if not matches["dob_match"]:
        score += 15
        reasons.append(
            "Date of birth does not match database"
        )

    if not matches["gender_match"]:
        score += 5
        reasons.append(
            "Gender does not match database"
        )

    if (
        matches.get("vid_available", True)
        and not matches["vid_match"]
    ):
        score += 25
        reasons.append(
            "VID does not match database"
        )

    score, reasons = add_forensic_score(
        score,
        reasons,
        forensic_data
    )

   

    return finalize_score(score, reasons)

def calculate_passport_score(matches, forensic_data):

    score = 0
    reasons = []




    if not matches["dob_match"]:
        score += 12
        reasons.append(
            "Date of birth does not match database"
        )

    if not matches["countrycode_match"]:
            score += 2
            reasons.append(
                "Country code does not match database"
            )

    if matches["name_similarity"] < 0.85:
            score += 15
            reasons.append(
                "Name does not sufficiently match database"
            )

    if matches["surname_similarity"] < 0.85:
            score += 15
            reasons.append(
                "Surname does not sufficiently match database"
            )
    

    

    if not matches["gender_match"]:
        score += 2
        reasons.append(
            "Gender does not match database"
        )

    if matches["nationality_similarity"] < 0.85:
                score += 5
                reasons.append(
                    "Nationality does not sufficiently match database"
                )

  

    if  not matches["dateOfIssue_match"]:
                    score += 7
                    reasons.append(
                        "Date of issue does not match database"
                    )

    if  not matches["dateOfExpiry_match"]:
                        score += 12
                        reasons.append(
                            "Date of expiry does not match database"
                        )

    

    score, reasons = add_forensic_passport(
        score,
        reasons,
        forensic_data
    )

   

    return finalize_score(score, reasons)


# =========================
# AADHAAR & PAN
# =========================

def add_forensic_score(score, reasons, forensic_data):

    if forensic_data.get("ela",0)*0.15>=7.5:

        score += forensic_data["ela"]*0.15
        
        reasons.append(
            "Suspicious ELA result"
        )

    if forensic_data.get("copy_move", 0)*0.10 >= 0.5:
        score += forensic_data["copy_move"]*0.10
        reasons.append(
            "Copy Move Detected"
        )

    if forensic_data.get("metadata", 0)*0.05>= 2.5:
        score += forensic_data["metadata"]*0.05
        reasons.append(
            "Metadata anomaly detected"
        )

    if forensic_data.get("noise", 0)*0.05>= 2.5:
            score += forensic_data["noise"]*0.05
            reasons.append(
                "Noise detected"
            )

    return score, reasons


# =========================
# PASSPORT
# =========================

def add_forensic_passport(score, reasons, forensic_data):

    if forensic_data.get("ela",0)*0.15>=7.5:

        score += forensic_data["ela"]*0.15
        
        reasons.append(
            "Suspicious ELA result"
        )

    if forensic_data.get("copy_move", 0)*0.08 >= 4.0:
        score += forensic_data["copy_move"]*0.08
        reasons.append(
            "Copy Move Detected"
        )

    if forensic_data.get("metadata", 0)*0.03>= 1.5:
        score += forensic_data["metadata"]*0.03
        reasons.append(
            "Metadata anomaly detected"
        )

    if forensic_data.get("noise", 0)*0.04>= 2.0:
            score += forensic_data["noise"]*0.04
            reasons.append(
                "Noise detected"
            )

    return score, reasons

def finalize_score(score, reasons):

    score = min(score, 100)

    if score >= 60:
        risk_level = "HIGH"
        decision = "REJECT"

    elif score >= 30:
        risk_level = "MEDIUM"
        decision = "REVIEW"

    else:
        risk_level = "LOW"
        decision = "ACCEPT"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "decision": decision,
        "reasons": reasons
    }