import re

def parse_id_data(ocr_text_list):
    full_text = " ".join(ocr_text_list)
    extracted_data = {}
    
    # 1. Extract Name (Line preceding DOB)
    for i, text in enumerate(ocr_text_list):
        if re.search(r'(DOB|Date of Birth|YOB|Year of Birth)', text, re.IGNORECASE):
            if i > 0:
                potential_name = ocr_text_list[i-1]
                clean_name = re.sub(r'[^a-zA-Z\s]', '', potential_name).strip()
                
                # Fallback if the line above was just garbage/empty
                if len(clean_name) < 3 and i > 1:
                    potential_name = ocr_text_list[i-2]
                    clean_name = re.sub(r'[^a-zA-Z\s]', '', potential_name).strip()
                    
                extracted_data['Name'] = clean_name
            break

    # 2. Extract Date of Birth
    dob_match = re.search(r'DOB.*?(\d{2}/\d{2}/\d{4})', full_text, re.IGNORECASE)
    extracted_data['DOB'] = dob_match.group(1) if dob_match else None
    
    # 3. Extract Gender
    gender_match = re.search(r'\b(MALE|FEMALE|TRANSGENDER)\b', full_text, re.IGNORECASE)
    extracted_data['Gender'] = gender_match.group(1) if gender_match else None
    
    # 4. Extract PIN Code
    pin_match = re.search(r'PIN Code:\s*(\d{6})', full_text, re.IGNORECASE)
    extracted_data['PIN'] = pin_match.group(1) if pin_match else None
    
    # 5. Extract Virtual ID (VID)
    vid_match = re.search(r'VID\s*[:;]?\s*(\d{4}\s\d{4}\s\d{4}\s\d{4})', full_text)
    extracted_data['VID'] = vid_match.group(1) if vid_match else None
    
    # 6. Extract 12-Digit ID Number
    extracted_data['ID_Number'] = None
    
    # ATTEMPT 1: Look for the specific heading
    # Handles variations like "YourAadhaarNo", "Your Aadhaar No:", "Aadhar No", etc.
    header_match = re.search(r'(?:Your\s*Aadhaar\s*No|Aadhaar\s*No|Aadhar\s*No|YourAadharNo)\.?\s*[:;-]?\s*(\d{4}\s\d{4}\s\d{4}|\d{12})', full_text, re.IGNORECASE)
    
    if header_match:
        raw_num = header_match.group(1)
        # If the OCR missed the spaces and grabbed 12 continuous digits, format it properly
        if len(raw_num) == 12 and " " not in raw_num:
            extracted_data['ID_Number'] = f"{raw_num[:4]} {raw_num[4:8]} {raw_num[8:]}"
        else:
            extracted_data['ID_Number'] = raw_num
            
    else:
        # ATTEMPT 2: Fallback logic (No heading detected)
        # Hunts for exactly: 4 digits, space, 4 digits, space, 4 digits
        spaced_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', full_text)
        
        if spaced_match:
            extracted_data['ID_Number'] = spaced_match.group(0)
            
        else:
            # ATTEMPT 3: Final fallback for a raw 12-digit continuous block
            continuous_match = re.search(r'\b\d{12}\b', full_text)
            if continuous_match:
                raw_num = continuous_match.group(0)
                extracted_data['ID_Number'] = f"{raw_num[:4]} {raw_num[4:8]} {raw_num[8:]}"

    return extracted_data

    
