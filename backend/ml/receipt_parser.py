"""Pull merchant, total and date out of receipt text (the output of local OCR).

Pure Python, no network. OCR itself is done by the Tesseract binary on the server
(see docs/RECEIPT_SCANNING.md). Results are suggestions the user confirms.
"""
import re
from datetime import date

_AMT = re.compile(r'(?:rs\.?|inr|\u20b9)?\s*(\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)', re.I)
_TOTAL_WORDS = re.compile(r'grand\s*total|total\s*(?:amount|due|payable)?|amount\s*(?:paid|payable|due)|net\s*(?:amount|payable)|bill\s*amount', re.I)
_SKIP_TOTAL = re.compile(r'sub\s*total|total\s*(?:items?|qty|quantity)|gst|tax|cgst|sgst|discount|saved', re.I)
_MONTHS = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}
_D_NUM = re.compile(r'\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b')
_D_ISO = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
_D_TXT = re.compile(r'\b(\d{1,2})[\s\-]([A-Za-z]{3})[a-z]*[\s\-,]*(\d{2,4})\b')


def _amounts(line):
    out = []
    for m in _AMT.finditer(line):
        try:
            v = float(m.group(1).replace(',', ''))
        except ValueError:
            continue
        if v > 0:
            out.append(v)
    return out


def _fix_year(y):
    return y + 2000 if y < 100 else y


def _valid(y, mo, d):
    try:
        date(y, mo, d)
        return True
    except ValueError:
        return False


def find_date(text):
    m = _D_ISO.search(text)
    if m and _valid(int(m.group(1)), int(m.group(2)), int(m.group(3))):
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = _D_NUM.search(text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), _fix_year(int(m.group(3)))
        if _valid(y, mo, d):  # Indian receipts are day first
            return f'{y:04d}-{mo:02d}-{d:02d}'
    m = _D_TXT.search(text)
    if m and m.group(2).lower() in _MONTHS:
        d, mo, y = int(m.group(1)), _MONTHS[m.group(2).lower()], _fix_year(int(m.group(3)))
        if _valid(y, mo, d):
            return f'{y:04d}-{mo:02d}-{d:02d}'
    return None


def find_total(lines):
    """Prefer the last 'total'-style line (skipping subtotal and tax lines); else the largest amount."""
    best = None
    for ln in lines:
        if _TOTAL_WORDS.search(ln) and not _SKIP_TOTAL.search(ln):
            a = _amounts(ln)
            if a:
                best = a[-1]
    if best is not None:
        return best, 'total line'
    every = [a for ln in lines for a in _amounts(ln) if not _D_NUM.search(ln)]
    return (max(every), 'largest amount') if every else (None, None)


def find_merchant(lines):
    for ln in lines[:6]:
        s = ln.strip(' *-_=#|')
        letters = sum(c.isalpha() for c in s)
        if len(s) >= 3 and letters >= 3 and letters / len(s) > 0.5 and not _TOTAL_WORDS.search(s) and not _D_NUM.search(s):
            return s[:120]
    return None


def parse_receipt(text):
    lines = [ln.strip() for ln in (text or '').splitlines() if ln.strip()]
    total, how = find_total(lines)
    return {
        'merchant': find_merchant(lines),
        'amount': total,
        'amount_source': how,
        'date': find_date(text or ''),
        'found': sum(x is not None for x in (total, find_merchant(lines), find_date(text or ''))),
    }
