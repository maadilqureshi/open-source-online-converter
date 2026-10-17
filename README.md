# ConvertKit Open — Open Source Online Converter

An open-source web application for converting common image and document formats. Built with Python, FastAPI, Pillow, PyMuPDF, python-docx, and LibreOffice.

## Supported conversions

| From | To |
|---|---|
| JPG/JPEG | PNG, WebP, PDF |
| PNG | JPG, WebP, PDF |
| WebP | JPG, PNG, PDF |
| BMP | JPG, PNG, WebP, PDF |
| DOCX | PDF |
| PDF (selectable text) | DOCX (text extraction only) |
| PDF | ZIP of PNG page images |

**Limitations:** PDF-to-DOCX is not a faithful layout reconstruction: tables, images, multi-column text, and scanned PDFs may not convert as expected. OCR is not implemented. Transparent image pixels become white when converting to JPG or PDF.

## Run with Docker (recommended)

```sh
docker build -t online-converter .
docker run --rm -p 8000:8000 online-converter
```

Open http://localhost:8000.

## Run locally

Requires Python 3.11+ and LibreOffice installed and available as `libreoffice` on the PATH:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows users can activate with `.venv\Scripts\activate`. LibreOffice is necessary for DOCX-to-PDF, not for most other conversions.

## Tests

```sh
pip install -r requirements-dev.txt
pytest -q
```

The GitHub Actions workflow runs automated tests on pushes and pull requests. Document-to-PDF availability additionally depends on LibreOffice being installed.

## Endpoints

- `GET /` — browser upload interface
- `GET /api/formats` — supported input/output formats
- `POST /api/convert` — multipart form fields `file` and `to`; returns converted binary data

## Security and operating limits

- Maximum uploaded file size: 15 MB.
- Maximum processed PDF length: 35 pages.
- Files are processed in memory or temporary folders and are not intentionally persisted.
- This starter service is **not hardened for untrusted public internet traffic**. Before deployment, add authentication or rate limiting, workload/resource isolation, content scanning as appropriate, request timeouts, observability and a reverse proxy.
- Avoid uploading personal, confidential, or sensitive documents to deployments you do not control.

## Hosting

GitHub Pages alone **cannot** host this full application because it requires a Python API and LibreOffice. Deploy the Docker image to a backend-capable service instead.

## Project layout

```text
app/        Backend endpoints and conversion routines
static/     Responsive upload UI and browser JavaScript
tests/      Automated conversion tests
Dockerfile  Container runtime with LibreOffice
```

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [MIT](LICENSE). Publishing the repository does not guarantee eligibility for third-party open-source programs.
