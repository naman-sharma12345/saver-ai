"""Parse a bank / UPI statement exported as CSV into expenses. Runs locally, no outside services.

Handles the usual Indian bank layouts: separate Debit/Credit columns, a single Amount column with
a Dr/Cr marker, and a few date formats. Credits (money in) are skipped.
"""
import csv
import io
import re
from datetime import date, datetime

MAX_ROWS = 2000

_DATE_FORMATS = ('%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%Y-%m-%d', '%d %b %Y', '%d-%b-%Y',
                 '%d %b %y', '%d-%b-%y', '%d.%m.%Y', '%m/%d/%Y')
_DATE_H = ('date', 'txn date', 'transaction date', 'value date', 'posting date')
_DESC_H = ('description', 'narration', 'particulars', 'details', 'remarks', 'transaction details',
           'transaction remarks', 'payee', 'merchant')
_DEBIT_H = ('debit', 'withdrawal', 'withdrawals', 'withdrawal amt', 'withdrawal amount', 'debit amount', 'dr')
_CREDIT_H = ('credit', 'deposit', 'deposits', 'deposit amt', 'deposit amount', 'credit amount', 'cr')
_AMOUNT_H = ('amount', 'transaction amount', 'amt')
_TYPE_H = ('type', 'dr/cr', 'cr/dr', 'transaction type', 'debit/credit')

_NOISE = re.compile(r'^(upi|imps|neft|rtgs|pos|ach|atm|ecom|nach|txn|ref|payment|to|by|from|transfer|dr|cr|paytm|ybl|oksbi|okaxis|okicici|okhdfcbank|ibl|axl|apl)$', re.I)


def parse_date(text):
    text = (text or '').strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(text):
    text = re.sub(r'[^\d.\-]', '', (text or '').replace(',', ''))
    if text in ('', '-', '.'):
        return None
    try:
        v = float(text)
    except ValueError:
        return None
    return v if v == v else None


def clean_merchant(narration):
    """Pull a readable merchant out of strings like 'UPI/402312345678/Zomato Ltd/zomato@icici/Food'."""
    parts = [p.strip() for p in re.split(r'[/|*\-@]+|\s{2,}', narration or '') if p.strip()]
    keep = [p for p in parts if not _NOISE.match(p) and not re.fullmatch(r'[\dXx*]{4,}', p) and not re.fullmatch(r'[A-Za-z]{0,4}\d{6,}', p)]
    name = keep[0] if keep else (narration or '').strip()
    return name[:60].strip() or 'Unknown'


def _find(headers, options):
    for i, h in enumerate(headers):
        if h in options:
            return i
    return None


def parse_statement(text):
    """Return {'rows': [{date, description, store_name, amount}], 'skipped': n, 'error': str|None}."""
    text = (text or '').lstrip('\ufeff')
    if not text.strip():
        return {'rows': [], 'skipped': 0, 'error': 'The file is empty.'}
    head = '\n'.join(text.splitlines()[:20])
    delim = max(',;\t|', key=head.count)
    table = [r for r in csv.reader(io.StringIO(text), delimiter=delim) if any(c.strip() for c in r)]

    # The header row is the first row that has a date column and a description column.
    hdr_i = idx = None
    for i, row in enumerate(table[:40]):
        names = [c.replace('.', '').strip().lower() for c in row]
        d, s = _find(names, _DATE_H), _find(names, _DESC_H)
        if d is not None and s is not None:
            hdr_i, idx = i, {'date': d, 'desc': s, 'debit': _find(names, _DEBIT_H), 'credit': _find(names, _CREDIT_H),
                             'amount': _find(names, _AMOUNT_H), 'type': _find(names, _TYPE_H)}
            break
    if idx is None or (idx['debit'] is None and idx['amount'] is None):
        return {'rows': [], 'skipped': 0,
                'error': 'Could not find the columns. We need Date, Description and Debit (or Amount).'}

    rows, skipped = [], 0
    for r in table[hdr_i + 1: hdr_i + 1 + MAX_ROWS]:
        cell = lambda k: r[idx[k]].strip() if idx[k] is not None and idx[k] < len(r) else ''
        d = parse_date(cell('date'))
        if d is None or d > date.today():
            skipped += 1
            continue
        amount = None
        if idx['debit'] is not None:
            amount = parse_amount(cell('debit'))
            if not amount and idx['credit'] is not None and parse_amount(cell('credit')):
                skipped += 1  # money in
                continue
        else:
            amount = parse_amount(cell('amount'))
            marker = cell('type').lower()
            if marker.startswith(('cr', 'credit')) or (amount is not None and amount < 0 and not marker):
                skipped += 1
                continue
        if not amount or amount <= 0:
            skipped += 1
            continue
        narration = cell('desc')
        rows.append({'date': d.isoformat(), 'description': narration[:255], 'store_name': clean_merchant(narration),
                     'amount': round(abs(amount), 2)})
    return {'rows': rows, 'skipped': skipped, 'error': None}
