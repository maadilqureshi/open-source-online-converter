"""FastAPI web app for file conversions."""
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .converters import ConversionError, convert_image, docx_to_pdf, pdf_to_docx, pdf_to_png_zip

ROOT = Path(__file__).resolve().parent.parent
MAX_UPLOAD = 15 * 1024 * 1024
CONVERSIONS = {
    "jpg": {"png", "webp", "pdf"},
    "jpeg": {"png", "webp", "pdf"},
    "png": {"jpg", "webp", "pdf"},
    "webp": {"jpg", "png", "pdf"},
    "bmp": {"jpg", "png", "webp", "pdf"},
    "docx": {"pdf"},
    "pdf": {"docx", "pngzip"},
}
MIMES = {
    "jpg": "image/jpeg", "png": "image/png", "webp": "image/webp",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pngzip": "application/zip",
}

app = FastAPI(title="Open Source Online Converter", version="1.0.0")
app.mount("/assets", StaticFiles(directory=ROOT / "static"), name="assets")


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/formats")
def formats():
    return {key: sorted(values) for key, values in CONVERSIONS.items()}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...), to: str = Form(...)):
    name = Path(file.filename or "document").name
    source = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    target = to.strip().lower()
    if target not in CONVERSIONS.get(source, set()):
        raise HTTPException(422, "Unsupported source/target combination")
    data = await file.read(MAX_UPLOAD + 1)
    await file.close()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Maximum file size is 15 MB")
    if not data:
        raise HTTPException(422, "Uploaded file is empty")
    try:
        if source in ("jpg", "jpeg", "png", "webp", "bmp"):
            output = convert_image(data, source, target)
        elif source == "docx":
            output = docx_to_pdf(data)
        elif target == "docx":
            output = pdf_to_docx(data)
        else:
            output = pdf_to_png_zip(data)
    except ConversionError as exc:
        raise HTTPException(422, str(exc)) from exc
    filename = f"{Path(name).stem[:80] or 'converted'}-converted.{('zip' if target == 'pngzip' else target)}"
    return Response(
        content=output, media_type=MIMES[target],
        headers={"Content-Disposition": f'attachment; filename="{filename}"',
                 "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
