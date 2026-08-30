import re

def extract_pan_info(ocr_text_list):
    full_text=" ".join(ocr_text_list)


    extracted_data={}

    for i,text in enumerate(ocr_text_list):

        if re.search(r'\bName\b', text, re.IGNORECASE) and not re.search(r'Father', text, re.IGNORECASE):
            if i + 1 < len(ocr_text_list):
                extracted_data['name'] = ocr_text_list[i+1].strip()

        if re.search(r'\bFather',text,re.IGNORECASE):
            if i+1<len(ocr_text_list):
                extracted_data['fathers_name']=ocr_text_list[i+1].strip()


    dob_match = re.search(
        r'\b(0[1-9]|[12]\d|3[01])\s*[/\-\|lI]\s*(0[1-9]|1[0-2])\s*[/\-\|lI]\s*(19\d{2}|20\d{2})\b', 
        full_text
    )
    
    if dob_match:
        day = dob_match.group(1)
        month = dob_match.group(2)
        year = dob_match.group(3)
        extracted_data['dob'] = f"{day}/{month}/{year}"
    else:
        extracted_data['dob'] = None

    pan_match=re.search(r'\b([A-Z]{5}\d{4}[A-Z]{1})\b',full_text,re.IGNORECASE)
    if pan_match:
        extracted_data['pan_num']=pan_match.group(1).upper()
    else:
        fallback_match = re.search(r'\b([A-Z0-9]{5}\d{4}[A-Z0-9]{1})\b', full_text, re.IGNORECASE)
        if fallback_match:
            raw_pan = fallback_match.group(1).upper()
            corrected_pan = list(raw_pan)
            
            for j in range(5):
                if corrected_pan[j] == '0': corrected_pan[j] = 'O'
                if corrected_pan[j] == '1': corrected_pan[j] = 'I'
            
            for j in range(5, 9):
                if corrected_pan[j] == 'O': corrected_pan[j] = '0'
                if corrected_pan[j] == 'I': corrected_pan[j] = '1'
                
            if corrected_pan[9] == '0': corrected_pan[9] = 'O'
            if corrected_pan[9] == '1': corrected_pan[9] = 'I'
            
            extracted_data['pan_num'] = "".join(corrected_pan)

    return extracted_data



