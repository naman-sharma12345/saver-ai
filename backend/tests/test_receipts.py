import base64
import io

import pytest

from ml.ocr import ocr_available
from ml.receipt_parser import parse_receipt, find_date
from tests.test_billing import _register, _auth

RECEIPT = """CAFE COFFEE DAY
12/10/2026 14:32
Cappuccino Rs 180.00
Sandwich Rs 120.00
Subtotal Rs 300.00
GST 5% Rs 15.00
TOTAL Rs 315.00
Paid via UPI"""


def test_parse_receipt():
    r = parse_receipt(RECEIPT)
    assert r['merchant'] == 'CAFE COFFEE DAY' and r['amount'] == 315.0 and r['date'] == '2026-10-12'
    assert r['amount_source'] == 'total line'


def test_parse_indian_grouping_and_text_date():
    r = parse_receipt('Big Bazaar\n5 Oct 2026\nGrand Total: \u20b9 1,249.50')
    assert r['amount'] == 1249.5 and r['date'] == '2026-10-05'


def test_falls_back_to_largest_amount():
    r = parse_receipt('Kirana Store\nMilk 60\nRice 540\nOil 210')
    assert r['amount'] == 540.0 and r['amount_source'] == 'largest amount'


def test_bad_dates_and_empty():
    assert find_date('31/02/2026') is None
    assert parse_receipt('')['found'] == 0


def test_endpoint_validation(client):
    h = _auth(_register(client, 'rc1@test.com')['access_token'])
    assert client.post('/api/expenses/receipt', json={}, headers=h).status_code == 400
    assert client.post('/api/expenses/receipt', json={'image_base64': '!!!'}, headers=h).status_code == 400
    assert client.post('/api/expenses/receipt').status_code == 401
    r = client.post('/api/expenses/receipt', json={'image_base64': base64.b64encode(b'not an image at all').decode()}, headers=h)
    assert r.status_code in (400, 503)


@pytest.mark.skipif(not ocr_available(), reason='tesseract not installed')
def test_endpoint_reads_receipt(client):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (560, 420), 'white')
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 24)
    except OSError:
        f = ImageFont.load_default()
    for i, ln in enumerate(RECEIPT.splitlines()):
        d.text((20, 20 + i * 48), ln, fill='black', font=f)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    h = _auth(_register(client, 'rc2@test.com')['access_token'])
    r = client.post('/api/expenses/receipt', json={'image_base64': base64.b64encode(buf.getvalue()).decode()}, headers=h)
    assert r.status_code == 200
    assert r.get_json()['amount'] == 315.0
