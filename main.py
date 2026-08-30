import os
import fitz 

os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"

from paddleocr import PaddleOCR
from preprocessor import DocumentProcessor 
from parser import parse_id_data
from parserpan import extract_pan_info
from passportparser import extract_passport_info

def convert_pdf_to_image(pdf_path, output_path="temp_page.png"):
    """Converts the first page of a PDF to a high-res PNG image."""
    print(f"Converting {pdf_path} to image...")
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    pix.save(output_path)
    doc.close()
    return output_path

def run_pipeline(image_path: str, doc_type: str):
    # 1. Preprocess
    print("Preprocessing image...")
    preprocessor = DocumentProcessor()

    processed_data = preprocessor.process(image_path)
    ocr_ready_image = processed_data["deskewed_color"]
    print("Running OCR...")
    ocr = PaddleOCR(lang="en")
    result = ocr.predict(ocr_ready_image)
    raw_texts = []
    for res in result:
        if isinstance(res, dict) and "rec_texts" in res:
            texts = res.get("rec_texts", [])
            raw_texts.extend(texts)
        else:
            print("Warning: Unexpected predict() output format.")
    for res in result:
        print(res)
    print("Parsing Data...")
    if doc_type == "pan":
        parsed_info = extract_pan_info(raw_texts)
    elif doc_type == "passport":
        parsed_info = extract_passport_info(raw_texts)
    else:
        parsed_info = parse_id_data(raw_texts)

    return parsed_info


def execution(filepath, doc_type):
    """Importable entry point -- runs unconditionally when called, unlike
    the previous version which only worked when this file was executed
    directly (because it wrapped its body in `if __name__ == "__main__":`,
    which is a module-level check, not a function-level one)."""
    target_file = filepath

    if not os.path.exists(target_file):
        print(f"CRITICAL ERROR: Cannot find '{target_file}'!")
        print(f"Make sure the file is located here: {os.getcwd()}")
        return None

    image_to_process = target_file

    if target_file.lower().endswith(".pdf"):
        image_to_process = convert_pdf_to_image(target_file, "temp_converted.png")

    final_data = run_pipeline(image_to_process, doc_type)

    # Cleanup now happens BEFORE return, so it actually executes
    if target_file.lower().endswith(".pdf") and os.path.exists(image_to_process):
        os.remove(image_to_process)

    return final_data


# This guard now correctly wraps only the "run this file directly for a
# quick manual test" case -- it no longer gates the function's real logic.
if __name__ == "__main__":
    result = execution("passporttest/test1.jpeg", "passport")
    print("\n--- Extraction Results ---")
    for key, value in result.items():
        print(f"{key}: {value}")