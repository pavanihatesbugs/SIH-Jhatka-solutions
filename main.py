import os
import fitz 

os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"

from paddleocr import PaddleOCR
from preprocessor import DocumentProcessor 
from parser import parse_id_data
from parserpan import extract_pan_info

def convert_pdf_to_image(pdf_path, output_path="temp_page.png"):
    """Converts the first page of a PDF to a high-res PNG image."""
    print(f"Converting {pdf_path} to image...")
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    pix.save(output_path)
    doc.close()
    return output_path

def run_pipeline(image_path: str,type):
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
    if type=="pan":
        parsed_info=extract_pan_info(raw_texts)
    else:
        parsed_info = parse_id_data(raw_texts)
    
    return parsed_info

#Execution block
if __name__ == "__main__":
    target_file = "pantest/chaidadpan.jpeg"
    type="pan"
    
    if not os.path.exists(target_file):
        print(f"CRITICAL ERROR: Cannot find '{target_file}'!")
        print(f"Make sure the PDF is located here: {os.getcwd()}")
        exit()

    image_to_process = target_file
    
    
    if target_file.lower().endswith(".pdf"):
        image_to_process = convert_pdf_to_image(target_file, "temp_converted.png")
    

    final_data = run_pipeline(image_to_process,type)
    
    print("\n--- Extraction Results ---")
    for key, value in final_data.items():
        print(f"{key}: {value}")

    if target_file.lower().endswith(".pdf") and os.path.exists(image_to_process):
        os.remove(image_to_process)