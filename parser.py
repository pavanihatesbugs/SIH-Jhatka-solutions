import re

def parse_id_data(ocr_text_list):
    full_text = " ".join(ocr_text_list)
    
    # TEMPORARY DEBUG: See exactly what the OCR engine thinks it sees
    print("\n--- DEBUG RAW OCR TEXT ---")
    print(full_text)
    print("--------------------------\n")
    
    extracted_data = {}
    
    for i, text in enumerate(ocr_text_list):
        if re.search(r'(DOB|Date of Birth|YOB|Year of Birth|తేది)', text, re.IGNORECASE):
            if i > 0:
                potential_name = ocr_text_list[i-1]
                clean_name = re.sub(r'[^a-zA-Z\s]', '', potential_name).strip()
                if clean_name=="Issue Date":
                    potential_name=ocr_text_list[i-2]
                    clean_name = re.sub(r'[^a-zA-Z\s]', '', potential_name).strip()
                if len(clean_name) < 3 and i > 1:
                    potential_name = ocr_text_list[i-2]
                    clean_name = re.sub(r'[^a-zA-Z\s]', '', potential_name).strip()

                    
                        
                extracted_data['name'] = clean_name
            break

    dob_match = re.search(r'(?:DOB|YOB|Year of Birth).*?(\d{2}/\d{2}/\d{4}|\d{4})', full_text, re.IGNORECASE)
    extracted_data['dob'] = dob_match.group(1) if dob_match else None
    
    gender_match = re.search(r'(MALE|FEMALE|TRANSGENDER|FEMAL|EMALE|PEMALE)', full_text, re.IGNORECASE)
    if gender_match:
        val = gender_match.group(1).upper()
        extracted_data['gender'] = "FEMALE" if "EMAL" in val else val
    else:
        extracted_data['gender'] = None

    # 5. Extract Virtual ID (VID)
    vid_match = re.search(r'VID\s*[:;]?\s*(\d{4}\s\d{4}\s\d{4}\s\d{4})', full_text)
    extracted_data['vid'] = vid_match.group(1) if vid_match else None
    
    # 6. Extract 12-Digit ID Number
    extracted_data['aadhaar_id'] = None
    
    search_text = full_text
    

    if extracted_data['dob']:
        search_text = search_text.replace(extracted_data['dob'], ' ')
        
        year_match = re.search(r'\d{4}', extracted_data['dob'])
        if year_match:
            search_text = search_text.replace(year_match.group(0), ' ')
    
    header_match = re.search(r'(?:Your\s*Aadhaar\s*No|Aadhaar\s*No|Aadhar\s*No|YourAadharNo)\.?\s*[:;-]?\s*(\d{4}\s\d{4}\s\d{4}|\d{12})', search_text, re.IGNORECASE)
    
    if header_match:
        raw_num = header_match.group(1)
        if len(raw_num) == 12 and " " not in raw_num:
            extracted_data['aadhaar_id'] = f"{raw_num[:4]}{raw_num[4:8]}{raw_num[8:]}"
        else:
            extracted_data['aadhaar_id'] = raw_num
            
    else:
        spaced_match = re.search(r'(?<!\d)(\d{4}\s\d{4}\s\d{4})(?!\d)', search_text)
        if spaced_match:
            extracted_data['aadhaar_id'] = spaced_match.group(1)
        else:
            continuous_match = re.search(r'(?<!\d)(\d{12})(?!\d)', search_text)
            if continuous_match:
                raw_num = continuous_match.group(1)
                extracted_data['aadhaar_id'] = f"{raw_num[:4]}{raw_num[4:8]}{raw_num[8:]}"

    return extracted_data