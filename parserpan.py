import re

def extract_pan_info(ocr_text_list):
    full_text="".join(ocr_text_list)

    # TEMPORARY DEBUG: See exactly what the OCR engine thinks it sees
    print("\n--- DEBUG RAW OCR TEXT ---")
    print(full_text)
    print("--------------------------\n")

    extracted_data={}

    for i,text in enumerate(ocr_text_list):

        if re.search(r'\bName\b', text, re.IGNORECASE) and not re.search(r'Father', text, re.IGNORECASE):
            if i + 1 < len(ocr_text_list):
                extracted_data['Name'] = ocr_text_list[i+1].strip()

        if re.search(r'\bFather',text,re.IGNORECASE):
            if i+1<len(ocr_text_list):
                extracted_data['Father Name']=ocr_text_list[i+1].strip()


        


    dob_match = re.search(r'(?:DOB|YOB|Year of Birth).*?(\d{2}/\d{2}/\d{4}|\d{4})', full_text, re.IGNORECASE)
    extracted_data['DOB'] = dob_match.group(1) if dob_match else None

    pan_match=re.search(r'\b[^A-Z]{5}[^0-9]{4}[^A-Z]{1}\b',full_text,re.IGNORECASE)
    if pan_match:
        extracted_data['Pan_Number']=pan_match.group(1).upper()
    else:
        fallback_match = re.search(r'\b([A-Z0-9]{5}\d{4}[A-Z0-9]{1})\b', full_text, re.IGNORECASE)
        if fallback_match:
            raw_pan = fallback_match.group(1).upper()
            corrected_pan = list(raw_pan)
            
            # First 5 characters must be letters
            for j in range(5):
                if corrected_pan[j] == '0': corrected_pan[j] = 'O'
                if corrected_pan[j] == '1': corrected_pan[j] = 'I'
            
            # Next 4 characters must be numbers
            for j in range(5, 9):
                if corrected_pan[j] == 'O': corrected_pan[j] = '0'
                if corrected_pan[j] == 'I': corrected_pan[j] = '1'
                
            # Last character must be a letter
            if corrected_pan[9] == '0': corrected_pan[9] = 'O'
            if corrected_pan[9] == '1': corrected_pan[9] = 'I'
            
            extracted_data['PAN_Number'] = "".join(corrected_pan)

    return extracted_data



