"""Turn a bank statement PDF into CSV text so the normal statement parser can read it.

Runs locally with pdfplumber (no outside services). Works for text PDFs that contain a table,
which covers most bank and UPI app exports. Scanned (image) PDFs are not supported.
"""
import base64
import binascii
import csv
import io

MAX_PDF_BYTES = 3_000_000
MAX_PAGES = 30


class PdfError(Exception):
    pass


def decode_pdf(b64):
    try:
        raw = base64.b64decode(b64, validate=False)
    except (binascii.Error, ValueError):
        raise PdfError('That PDF could not be read.')
    if len(raw) > MAX_PDF_BYTES:
        raise PdfError('That PDF is too large (3 MB max).')
    if not raw.startswith(b'%PDF'):
        raise PdfError('That file is not a PDF.')
    return raw


def pdf_to_csv(raw):
    try:
        import pdfplumber
    except ImportError:
        raise PdfError('PDF import is not enabled on this server. Upload a CSV instead.')
    rows = []
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages[:MAX_PAGES]:
                for table in page.extract_tables() or []:
                    for row in table:
                        cells = [(c or '').replace('\n', ' ').strip() for c in row]
                        if any(cells):
                            rows.append(cells)
    except Exception:
        raise PdfError('That PDF could not be read. Try exporting a CSV instead.')
    if not rows:
        raise PdfError('No transaction table found in that PDF. Scanned PDFs are not supported, try a CSV.')
    out = io.StringIO()
    csv.writer(out).writerows(rows)
    return out.getvalue()
