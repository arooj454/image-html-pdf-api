from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from PIL import Image
import io
import os
import tempfile
import pdfkit

app = FastAPI(title="File & Image Converter API")

UPLOAD_FOLDER = tempfile.gettempdir()

def get_temp_file(filename: str):
    return os.path.join(UPLOAD_FOLDER, filename)

# ===== Image Conversion Routes =====
@app.post("/png-to-jpg")
async def png_to_jpg(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Only PNG files allowed")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGB")
        output_stream = io.BytesIO()
        output_stream.name = file.filename.replace(".png", ".jpg")
        img.save(output_stream, format="JPEG")
        output_stream.seek(0)
        return StreamingResponse(
            output_stream,
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename={output_stream.name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jpg-to-png")
async def jpg_to_png(file: UploadFile = File(...)):
    if not (file.filename.lower().endswith(".jpg") or file.filename.lower().endswith(".jpeg")):
        raise HTTPException(status_code=400, detail="Only JPG files allowed")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        output_stream = io.BytesIO()
        output_stream.name = file.filename.rsplit(".", 1)[0] + ".png"
        img.save(output_stream, format="PNG")
        output_stream.seek(0)
        return StreamingResponse(
            output_stream,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={output_stream.name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Photo to PDF Route =====
@app.post("/photo-to-pdf")
async def photo_to_pdf(files: list[UploadFile] = File(...)):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Please upload at least one image.")
    images = []
    allowed = [".jpg", ".jpeg", ".png", ".webp"]
    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
            content = await file.read()
            img = Image.open(io.BytesIO(content)).convert("RGB")
            images.append(img)
        output_pdf = io.BytesIO()
        images[0].save(
            output_pdf,
            format="PDF",
            save_all=True,
            append_images=images[1:] if len(images) > 1 else None,
        )
        output_pdf.seek(0)
        return StreamingResponse(
            output_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=photos_converted.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert images: {str(e)}")

# ===== HTML to PDF Route =====
@app.post("/html-to-pdf")
async def html_to_pdf(html_content: str = Form(...)):
    try:
        output_pdf = io.BytesIO()
        pdfkit.from_string(html_content, output_pdf)
        output_pdf.seek(0)
        return StreamingResponse(
            output_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=html_converted.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert HTML to PDF: {str(e)}")
