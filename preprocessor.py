import cv2
import numpy as np
import os
import fitz



class DocumentProcessor:
    def __init__(self,target_dpi:  int=300,max_dim: int=1500):
        self.target_dpi = target_dpi
        self.max_dim = max_dim
    def load_document(self, file_path: str) -> np.ndarray:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Unable to decode image file: {file_path}")
        
        return self.scale_image(img)

    def scale_image(self, img: np.ndarray) -> np.ndarray:
        """Scales image down if it exceeds max_dim to speed up OCR."""
        height, width = img.shape[:2]
        if max(height, width) > self.max_dim:
            scale = max(height, width) / self.max_dim
            new_width = int(width / scale)
            new_height = int(height / scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return img

    def compute_skew_angle(self, gray_image: np.ndarray) -> float:
        thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if coords.size == 0:
            return 0.0

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle
        return angle

    def rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        cos, sin = np.abs(matrix[0, 0]), np.abs(matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        matrix[0, 2] += (new_w / 2) - center[0]
        matrix[1, 2] += (new_h / 2) - center[1]

        return cv2.warpAffine(image, matrix, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def process(self, file_path: str) -> dict:
        raw_bgr = self.load_document(file_path)
        gray = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2GRAY)
        
        # Denoise and deskew
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        skew_angle = self.compute_skew_angle(denoised)
        
        deskewed_bgr = self.rotate_image(raw_bgr, skew_angle) if abs(skew_angle) > 0.5 else raw_bgr
        
        return {
            "raw_original": raw_bgr,
            "deskewed_color": deskewed_bgr, # PaddleOCR performs best on color/deskewed images
            "skew_angle": skew_angle
        }
    