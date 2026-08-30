from .matcher import compare_pan, compare_aadhaar,compare_passport
from .scorer import calculate_pan_score,calculate_aadhaar_score,calculate_passport_score





def run_fraud_engine(
    document_type,
    ocr_data,
    db_data,
    forensic_data
):

 

    # =========================
    # PAN
    # =========================

    if document_type.upper() == "PAN":

        matches = compare_pan(
            ocr_data,
            db_data
        )

       
       

        result = calculate_pan_score(
            matches,
            forensic_data,
           
        )

        return {
            "document_type": "PAN",


            "field_checks": {
                

                "name_similarity":
                    matches["name_similarity"],

                "father_similarity":
                    matches["father_similarity"],

                "dob":
                    "MATCH"
                    if matches["dob_match"]
                    else "MISMATCH"
            },

            "forensic_checks": forensic_data,

        

            **result
        }

    # =========================
    # AADHAAR
    # =========================

    elif document_type.upper() == "AADHAAR":

        matches = compare_aadhaar(
            ocr_data,
            db_data
        )

       
       

        result = calculate_aadhaar_score(
            matches,
            forensic_data,
          
        )

        return {
            "document_type": "AADHAAR",

            "field_checks": {
                

                "name_similarity":
                    matches["name_similarity"],

                "dob":
                    "MATCH"
                    if matches["dob_match"]
                    else "MISMATCH",

                "gender":
                    "MATCH"
                    if matches["gender_match"]
                    else "MISMATCH",

                "vid":
                    "MATCH"
                    if matches["vid_match"]
                    else "MISMATCH"
            },

            "forensic_checks": forensic_data,

            **result
        }

    # =========================
    # PASSPORT
    # =========================

    elif document_type.upper() == "PASSPORT":
    
            matches = compare_passport(
                ocr_data,
                db_data
            )
    
           
           
    
            result = calculate_passport_score(
                matches,
                forensic_data
              
            )
    
            return {
                "document_type": "PASSPORT",
    
                "field_checks": {
                    
                        

                    "countrycode":
                        "MATCH"
                        if matches["countrycode_match"]
                        else "MISMATCH",

                    "surname_similarity":
                            matches["surname_similarity"],

                    "name_similarity":
                        matches["name_similarity"],

                    "nationality_similarity":
                        matches["nationality_similarity"],
    
    
                    "gender":
                        "MATCH"
                        if matches["gender_match"]
                        else "MISMATCH",

                    "dob":
                        "MATCH"
                        if matches["dob_match"]
                        else "MISMATCH",

                    "dateOfIssue":
                        "MATCH"
                        if matches["dob_match"]
                        else "MISMATCH",

                    "dateOfExpiry":
                        "MATCH"
                        if matches["dob_match"]
                        else "MISMATCH"





            },
    
                "forensic_checks": forensic_data,
    
                **result
            }

    else:

        raise ValueError(
            f"Unsupported document type: {document_type}"
        )