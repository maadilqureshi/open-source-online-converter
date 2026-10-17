from io import BytesIO
import zipfile
import fitz
import pytest
from PIL import Image
from docx import Document
from app.converters import convert_image, pdf_to_docx, pdf_to_png_zip, ConversionError


def image_bytes(fmt="PNG"):
    out = BytesIO()
    Image.new("RGB", (12, 8), "red").save(out, format=fmt)
    return out.getvalue()


def sample_pdf():
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((60, 60), "Hello converter")
    result = pdf.tobytes()
    pdf.close()
    return result


def test_png_to_jpeg():
    output = convert_image(image_bytes(), "png", "jpg")
    assert Image.open(BytesIO(output)).format == "JPEG"


def test_jpeg_to_png():
    output = convert_image(image_bytes("JPEG"), "jpg", "png")
    assert Image.open(BytesIO(output)).format == "PNG"


def test_png_to_webp():
    output = convert_image(image_bytes(), "png", "webp")
    assert Image.open(BytesIO(output)).format == "WEBP"


def test_image_to_pdf():
    assert fitz.open(stream=convert_image(image_bytes(), "png", "pdf"), filetype="pdf").page_count == 1


def test_invalid_image():
    with pytest.raises(ConversionError):
        convert_image(b"bad", "png", "jpg")


def test_invalid_image_format():
    with pytest.raises(ConversionError):
        convert_image(image_bytes(), "gif", "jpg")


def test_pdf_to_word():
    output = pdf_to_docx(sample_pdf())
    document = Document(BytesIO(output))
    assert "Hello converter" in "\n".join(p.text for p in document.paragraphs)


def test_pdf_to_png_zip():
    with zipfile.ZipFile(BytesIO(pdf_to_png_zip(sample_pdf()))) as archive:
        assert archive.namelist() == ["page-001.png"]
        assert archive.read("page-001.png").startswith(b"\x89PNG")


def test_invalid_pdf():
    with pytest.raises(ConversionError):
        pdf_to_docx(b"not a pdf")


def test_blank_pdf():
    pdf = fitz.open()
    pdf.new_page()
    data = pdf.tobytes()
    pdf.close()
    with pytest.raises(ConversionError):
        pdf_to_docx(data)


def test_pdf_zip_invalid():
    with pytest.raises(ConversionError):
        pdf_to_png_zip(b"not a pdf")
