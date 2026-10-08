from ml.statement_parser import parse_statement, clean_merchant, parse_date

HDFC = (
    "Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
    "01/09/26,UPI-ZOMATO-ZOMATO@ICICI-402312345678-Food,0000402312345678,01/09/26,\"1,250.50\",,8000\n"
    "02/09/26,UPI-RAHUL SHARMA-RAHUL@OKSBI-402399999999-Pocket money,0000,02/09/26,,5000.00,13000\n"
    "03/09/26,NEFT-UBER INDIA-TRIP,0000,03/09/26,230.00,,12770\n"
)

SINGLE = (
    "Account statement\n"
    "Txn Date;Description;Amount;Dr/Cr\n"
    "2026-09-05;Spotify India;119;DR\n"
    "2026-09-06;Refund Amazon;300;CR\n"
)


def test_two_column_statement():
    p = parse_statement(HDFC)
    assert p['error'] is None and len(p['rows']) == 2 and p['skipped'] == 1
    assert p['rows'][0]['amount'] == 1250.5 and p['rows'][0]['date'] == '2026-09-01'
    assert p['rows'][0]['store_name'].lower() == 'zomato'


def test_single_amount_column_skips_credits():
    p = parse_statement(SINGLE)
    assert [r['store_name'] for r in p['rows']] == ['Spotify India'] and p['skipped'] == 1


def test_bad_file():
    assert parse_statement('')['error']
    assert parse_statement('foo,bar\n1,2\n')['error']


def test_helpers():
    assert parse_date('5 Sep 2026').isoformat() == '2026-09-05'
    assert clean_merchant('UPI/402312345678/Swiggy Instamart/swiggy@axl') == 'Swiggy Instamart'


def test_import_preview_commit_and_dedupe(client, auth_headers):
    r = client.post('/api/expenses/import', json={'csv': HDFC}, headers=auth_headers)
    body = r.get_json()
    assert r.status_code == 200 and len(body['rows']) == 2 and all(x['category'] for x in body['rows'])
    r = client.post('/api/expenses/import', json={'csv': HDFC, 'commit': True}, headers=auth_headers)
    assert r.status_code == 201 and r.get_json()['imported'] == 2
    again = client.post('/api/expenses/import', json={'csv': HDFC, 'commit': True}, headers=auth_headers)
    assert again.get_json()['imported'] == 0 and again.get_json()['duplicates'] == 2


def test_import_requires_auth_and_csv(client, auth_headers):
    assert client.post('/api/expenses/import', json={'csv': HDFC}).status_code == 401
    assert client.post('/api/expenses/import', json={}, headers=auth_headers).status_code == 400


def test_user_entered_expense_date(client, auth_headers):
    r = client.post('/api/expenses', json={'amount': 40, 'description': 'chai', 'store_name': 'Stall', 'date': '2026-01-15'}, headers=auth_headers)
    assert r.status_code == 201 and r.get_json()['expense']['created_at'].startswith('2026-01-15')
    assert client.post('/api/expenses', json={'amount': 40, 'description': 'x', 'store_name': 'y', 'date': '2999-01-01'}, headers=auth_headers).status_code == 400


def _make_pdf(rows):
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors
    buf = io.BytesIO()
    t = Table(rows)
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
    SimpleDocTemplate(buf, pagesize=A4).build([t])
    return buf.getvalue()


def test_pdf_statement_import(client, auth_headers):
    import base64
    pdf = _make_pdf([
        ['Date', 'Narration', 'Withdrawal Amt.', 'Deposit Amt.'],
        ['01/09/26', 'UPI-ZOMATO-ZOMATO@ICICI-4023', '1250.50', ''],
        ['02/09/26', 'UPI-RAHUL-Pocket money', '', '5000.00'],
        ['03/09/26', 'NEFT-OLA CABS-RIDE', '230.00', ''],
    ])
    b64 = base64.b64encode(pdf).decode()
    r = client.post('/api/expenses/import', json={'pdf_base64': b64}, headers=auth_headers)
    body = r.get_json()
    assert r.status_code == 200, body
    assert len(body['rows']) == 2 and body['skipped'] == 1 and body['total'] == 1480.5
    r = client.post('/api/expenses/import', json={'pdf_base64': b64, 'commit': True}, headers=auth_headers)
    assert r.status_code == 201 and r.get_json()['imported'] == 2


def test_pdf_rejects_non_pdf_and_empty_tables(client, auth_headers):
    import base64
    bad = base64.b64encode(b'hello world').decode()
    assert client.post('/api/expenses/import', json={'pdf_base64': bad}, headers=auth_headers).status_code == 400
    from reportlab.pdfgen import canvas
    import io
    buf = io.BytesIO(); c = canvas.Canvas(buf); c.drawString(100, 700, 'no table here'); c.save()
    r = client.post('/api/expenses/import', json={'pdf_base64': base64.b64encode(buf.getvalue()).decode()}, headers=auth_headers)
    assert r.status_code == 400 and 'table' in r.get_json()['error']
