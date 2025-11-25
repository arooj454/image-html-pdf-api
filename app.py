from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, Response
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
        img.save(output_stream, format="JPEG", quality=95)
        output_stream.seek(0)
        
        filename = file.filename.replace(".png", ".jpg")
        
        return Response(
            content=output_stream.getvalue(),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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
        img.save(output_stream, format="PNG")
        output_stream.seek(0)
        
        filename = file.filename.rsplit(".", 1)[0] + ".png"
        
        return Response(
            content=output_stream.getvalue(),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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
        
        return Response(
            content=output_pdf.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=photos_converted.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert images: {str(e)}")

# ===== HTML to PDF Route =====
@app.post("/html-to-pdf")
async def html_to_pdf(html_content: str = Form(...)):
    try:
        # Configure pdfkit options
        options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'quiet': ''
        }
        
        # Create temporary file for PDF
        temp_pdf = os.path.join(tempfile.gettempdir(), 'temp_output.pdf')
        
        # Generate PDF from HTML string
        pdfkit.from_string(html_content, temp_pdf, options=options)
        
        # Read the generated PDF
        with open(temp_pdf, 'rb') as f:
            pdf_content = f.read()
        
        # Clean up temp file
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=html_converted.pdf"}
        )
    except Exception as e:
        # Clean up temp file in case of error
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        raise HTTPException(status_code=500, detail=f"Failed to convert HTML to PDF: {str(e)}")

# ===== Health Check Route =====
@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "File & Image Converter API",
        "endpoints": {
            "/png-to-jpg": "Convert PNG to JPG",
            "/jpg-to-png": "Convert JPG to PNG",
            "/photo-to-pdf": "Convert images to PDF",
            "/html-to-pdf": "Convert HTML to PDF"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
