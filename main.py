import os
# Set environment variables before importing PaddleOCR
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"

from paddleocr import PaddleOCR
# Ensure the class name here matches what is in your preprocessor.py file!
from preprocessor import DocumentProcessor 
from parser import parse_id_data

def run_pipeline(image_path: str):
    # 1. Preprocess
    print("Preprocessing image...")
    preprocessor = DocumentProcessor()
    processed_data = preprocessor.process(image_path)
    ocr_ready_image = processed_data["deskewed_color"]
    
    # 2. OCR Extraction
    print("Running OCR...")
    ocr = PaddleOCR(lang="en")
    
    # 3. Run Inference using predict
    result = ocr.predict(ocr_ready_image)
    
    # 4. Extract text using your original predict structure
    raw_texts = []
    for res in result:
        # Check if it's a dictionary with 'rec_texts' (based on your original code)
        if isinstance(res, dict) and "rec_texts" in res:
            texts = res.get("rec_texts", [])
            raw_texts.extend(texts)
        else:
            # Fallback just in case predict returns standard list structures
            print("Warning: Unexpected predict() output format.")
            
    # 5. Parse Data (This was missing)
    print("Parsing Data...")
    parsed_info = parse_id_data(raw_texts)
    
    return parsed_info  # (This was missing)

# 6. Execution block (Must be completely flush with the left margin)
if __name__ == "__main__":
    # Test your local execution
    target_image = "images/testcase5.jpg"
    final_data = run_pipeline(target_image)
    
    print("\n--- Extraction Results ---")
    for key, value in final_data.items():
        print(f"{key}: {value}")

