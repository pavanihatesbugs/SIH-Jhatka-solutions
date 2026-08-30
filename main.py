import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from forensics.analyzer import analyze_forensics

app = FastAPI(
    title="Document Forensics API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Document Forensics API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...)
):
    try:
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "No filename provided"
                }
            )

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".bmp"
        }

        extension = os.path.splitext(
            file.filename
        )[1].lower()

        if extension not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Unsupported image format"
                }
            )

        os.makedirs("uploads", exist_ok=True)

        safe_name = os.path.basename(
            file.filename
        )

        input_path = os.path.join(
            "uploads",
            safe_name
        )

        contents = await file.read()

        with open(
            input_path,
            "wb"
        ) as f:
            f.write(contents)

        result = analyze_forensics(
            input_path
        )

        return result

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )