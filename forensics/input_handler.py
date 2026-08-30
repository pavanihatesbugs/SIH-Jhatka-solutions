import os
import cv2
import pymupdf


SUPPORTED_IMAGE_TYPES = [".jpg", ".jpeg", ".png"]


def load_image(file_path):
    """
    Load a JPG, JPEG or PNG image.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension not in SUPPORTED_IMAGE_TYPES:
        return None

    image = cv2.imread(file_path)

    return image


def convert_pdf_to_images(pdf_path, output_folder="working"):
    """
    Convert every page of a PDF into a PNG image.
    """

    os.makedirs(output_folder, exist_ok=True)

    pdf = pymupdf.open(pdf_path)

    image_paths = []

    for page_number in range(len(pdf)):

        page = pdf[page_number]

        pixmap = page.get_pixmap()

        output_path = os.path.join(
            output_folder,
            f"page_{page_number + 1}.png"
        )

        pixmap.save(output_path)

        image_paths.append(output_path)

    pdf.close()

    return image_paths