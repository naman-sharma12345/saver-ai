"""Run the local Tesseract binary on an image. No network, no API keys."""
import shutil
import subprocess
import tempfile

MAX_BYTES = 5 * 1024 * 1024
_MAGIC = (b'\x89PNG', b'\xff\xd8\xff', b'II*\x00', b'MM\x00*', b'BM')


class OcrUnavailable(Exception):
    pass


class OcrError(Exception):
    pass


def ocr_available():
    return shutil.which('tesseract') is not None


def looks_like_image(data):
    return data[:4].startswith(_MAGIC) or data[:12].startswith(b'RIFF') and data[8:12] == b'WEBP'


def image_to_text(data):
    if not ocr_available():
        raise OcrUnavailable('Receipt scanning is not set up on this server yet')
    if len(data) > MAX_BYTES:
        raise OcrError('That image is too large (5 MB max)')
    if not looks_like_image(data):
        raise OcrError('Upload a PNG, JPG, WebP, TIFF or BMP photo of the receipt')
    with tempfile.NamedTemporaryFile(suffix='.img') as f:
        f.write(data)
        f.flush()
        try:
            r = subprocess.run(['tesseract', f.name, '-', '--psm', '6'], capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            raise OcrError('Reading that image took too long. Try a smaller photo.')
    if r.returncode != 0:
        raise OcrError('Could not read that image')
    return r.stdout.decode('utf-8', 'replace')
