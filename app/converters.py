"""Conversion functions; temporary document files are cleaned up after processing."""
from io import BytesIO
from pathlib import Path
import subprocess
import tempfile
import zipfile

import fitz
from docx import Document
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PAGES = 35


class ConversionError(ValueError):
    pass


def convert_image(data: bytes, source: str, dest: str) -> bytes:
    if source not in ("jpg", "jpeg", "png", "webp", "bmp") or dest not in ("jpg", "png", "webp", "pdf"):
        raise ConversionError("Unsupported image format")
    try:
        with Image.open(BytesIO(data)) as original:
            original.load()
            image = ImageOps.exif_transpose(original)
            if image.width * image.height > 45_000_000:
                raise ConversionError("Image is too large")
            if dest in ("jpg", "pdf"):
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGBA")
            output = BytesIO()
            fmt = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP", "pdf": "PDF"}[dest]
            options = {"quality": 92} if dest in ("jpg", "webp") else {}
            image.save(output, format=fmt, **options)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        if isinstance(exc, ConversionError):
            raise
        raise ConversionError("Invalid or unsupported image file") from exc


def docx_to_pdf(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="converter-") as folder:
        root = Path(folder)
        infile = root / "document.docx"
        infile.write_bytes(data)
        profile = (root / "profile").resolve().as_uri()
        try:
            result = subprocess.run(
                ["libreoffice", f"-env:UserInstallation={profile}", "--headless",
                 "--convert-to", "pdf:writer_pdf_Export", "--outdir", str(root), str(infile)],
                capture_output=True, text=True, timeout=45, check=False,
            )
        except FileNotFoundError as exc:
            raise ConversionError("Word conversion engine is not installed on this server") from exc
        except subprocess.TimeoutExpired as exc:
            raise ConversionError("Word conversion took too long") from exc
        outfile = root / "document.pdf"
        if result.returncode != 0 or not outfile.exists():
            raise ConversionError("Could not convert this DOCX file")
        return outfile.read_bytes()


def pdf_to_docx(data: bytes) -> bytes:
    try:
        with fitz.open(stream=data, filetype="pdf") as pdf:
            if pdf.is_encrypted:
                raise ConversionError("Password-protected PDFs are unsupported")
            if not 1 <= len(pdf) <= MAX_PAGES:
                raise ConversionError(f"PDF must have between 1 and {MAX_PAGES} pages")
            document = Document()
            found = False
            for index, page in enumerate(pdf):
                if index:
                    document.add_page_break()
                for block in page.get_text("blocks", sort=True):
                    if len(block) < 7 or block[6] != 0:
                        continue
                    text = block[4].strip()
                    if text:
                        found = True
                        document.add_paragraph(text)
            if not found:
                raise ConversionError("No extractable text. Scanned PDFs need OCR, which is not supported.")
            output = BytesIO()
            document.save(output)
            return output.getvalue()
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ConversionError("Invalid PDF document") from exc


def pdf_to_png_zip(data: bytes) -> bytes:
    try:
        with fitz.open(stream=data, filetype="pdf") as pdf:
            if pdf.is_encrypted:
                raise ConversionError("Password-protected PDFs are unsupported")
            if not 1 <= len(pdf) <= MAX_PAGES:
                raise ConversionError(f"PDF must have between 1 and {MAX_PAGES} pages")
            output = BytesIO()
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
                for number, page in enumerate(pdf, start=1):
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    archive.writestr(f"page-{number:03d}.png", pixmap.tobytes("png"))
            return output.getvalue()
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ConversionError("Invalid PDF document") from exc
