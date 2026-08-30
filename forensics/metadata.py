import os

from PIL import Image
from PIL.ExifTags import TAGS


def analyze_image_metadata(image_path):

    extension = os.path.splitext(image_path)[1].lower()

    if extension not in [".jpg", ".jpeg", ".png"]:
        return {
            "success": False,
            "message": "Metadata analysis currently supports images only"
        }

    try:
        image = Image.open(image_path)

        metadata = {}

        exif_data = image.getexif()

        for tag_id, value in exif_data.items():

            tag_name = TAGS.get(tag_id, tag_id)

            metadata[tag_name] = str(value)

        return {
            "success": True,
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "metadata": metadata
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }


def analyze_pdf_metadata(pdf_path):

    try:
        import pymupdf

        pdf = pymupdf.open(pdf_path)

        metadata = pdf.metadata

        page_count = len(pdf)

        pdf.close()

        return {
            "success": True,
            "page_count": page_count,
            "metadata": metadata
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }