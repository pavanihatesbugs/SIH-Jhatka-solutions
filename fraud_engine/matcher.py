from rapidfuzz.fuzz import ratio


def normalize_text(value):

    if value is None:
        return ""

    return " ".join(
        str(value).upper().strip().split()
    )


def similarity(a, b):

    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    return ratio(a, b) / 100.0


def compare_pan(ocr_data, db_data):

    return {
        

        "name_similarity":
            similarity(
                ocr_data.get("name"),
                db_data.get("name")
            ),

        "father_similarity":
            similarity(
                ocr_data.get("fathers_name"),
                db_data.get("fathers_name")
            ),

        "dob_match":
            normalize_text(ocr_data.get("dob"))
            == normalize_text(db_data.get("dob"))
    }


def compare_aadhaar(ocr_data, db_data):

    ocr_vid = normalize_text(ocr_data.get("vid"))
    db_vid = normalize_text(db_data.get("vid"))

    return {
        

        "name_similarity":
            similarity(
                ocr_data.get("name"),
                db_data.get("name")
            ),

        "dob_match":
            normalize_text(ocr_data.get("dob"))
            == normalize_text(db_data.get("dob")),

        "gender_match":
            normalize_text(ocr_data.get("gender"))
            == normalize_text(db_data.get("gender")),

        "vid_match":
            ocr_vid == db_vid,

        "vid_available":
            bool(ocr_vid) and bool(db_vid)
    }


def compare_passport(ocr_data, db_data):

    

    return {
        



        "countrycode_match":
                    normalize_text(ocr_data.get("country_code"))
                    == normalize_text(db_data.get("country_code")),


        "surname_similarity":
                    similarity(
                        ocr_data.get("surname"),
                        db_data.get("surname")
                    ),

        "name_similarity":
                    similarity(
                        ocr_data.get("name"),
                        db_data.get("name")
                    ),
        "nationality_similarity":
                similarity(
                            ocr_data.get("nationality"),
                            db_data.get("nationality")
                        )
                   ,

        "gender_match":
            normalize_text(ocr_data.get("gender"))
            == normalize_text(db_data.get("gender")),

        "dob_match":
                    normalize_text(ocr_data.get("dob"))
                    == normalize_text(db_data.get("dob")),

       

        "dateOfIssue_match":
                            normalize_text(ocr_data.get("dateOFIssue"))
                            == normalize_text(db_data.get("dateOfIssue")),

        "dateOfExpiry_match":
                            normalize_text(ocr_data.get("dateOfExpiry"))
                            == normalize_text(db_data.get("dateOfExpiry")),

                            
        

            


            
                   

      
    }