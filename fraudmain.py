from fastapi import FastAPI,HTTPException
from doc_retreival.database import get_pan_record, get_aadhaar_record,get_passport_record
from fraud_engine.engine import run_fraud_engine


app = FastAPI()


@app.post("/fraud/pan")
def check_pan(data: dict):

 
    ocr_data = data["ocr_data"]


    forensic_data = data["forensic_data"]

    
    pan_num = ocr_data.get("pan_num")

    if not pan_num:
        raise HTTPException(
            status_code=400,
            detail="PAN number not found in OCR data"
        )

   
    db_data = get_pan_record(pan_num)

    if db_data is None:
        raise HTTPException(
            status_code=404,
            detail="PAN record not found/Invalid"
        )

   
    result = run_fraud_engine(
        document_type="PAN",
        ocr_data=ocr_data,
        db_data=db_data,
        forensic_data=forensic_data
    )

    return result

@app.post("/fraud/aadhaar")
def check_aadhaar(data: dict):

    ocr_data = data["ocr_data"]

    forensic_data = data["forensic_data"]

    aadhaar_id = ocr_data.get("aadhaar_id")

    if not aadhaar_id:
        raise HTTPException(
            status_code=400,
            detail="Aadhaar number not found in OCR data"
        )

    
    db_data = get_aadhaar_record(aadhaar_id)

    if db_data is None:
        raise HTTPException(
            status_code=404,
            detail="Aadhaar record not found/Invalid"
        )

    result = run_fraud_engine(
        document_type="AADHAAR",
        ocr_data=ocr_data,
        db_data=db_data,
        forensic_data=forensic_data
    )

    return result


@app.post("/fraud/passport")
def check_passport(data: dict):

    ocr_data = data["ocr_data"]

    forensic_data = data["forensic_data"]

    passport_num = ocr_data.get("passport_num")

    if not passport_num:
        raise HTTPException(
            status_code=400,
            detail="Passport number not found in OCR data"
        )

    
    db_data = get_passport_record(passport_num)

    if db_data is None:
        raise HTTPException(
            status_code=404,
            detail="Passport record not found/Invalid"
        )

    result = run_fraud_engine(
        document_type="PASSPORT",
        ocr_data=ocr_data,
        db_data=db_data,
        forensic_data=forensic_data
    )

    return result