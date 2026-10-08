"""POST /api/expenses/import - bring in a bank/UPI statement (CSV text or a PDF).

Body: {"csv": "<file text>"} or {"pdf_base64": "<PDF bytes, base64>"}, plus "commit": false
 - commit false (default): preview only, nothing is saved.
 - commit true: save the new rows. Rows already imported (same date, amount and description) are skipped.
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import Expense
from ml.categorizer import predict_category
from ml.category_rules import rule_category
from ml.statement_parser import parse_statement
from ml.pdf_statement import PdfError, decode_pdf, pdf_to_csv

imports_bp = Blueprint('imports', __name__)

MAX_CHARS = 1_000_000


@imports_bp.route('/expenses/import', methods=['POST'])
@jwt_required()
def import_statement():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    text = data.get('csv')
    pdf_b64 = data.get('pdf_base64')
    if isinstance(pdf_b64, str) and pdf_b64:
        try:
            text = pdf_to_csv(decode_pdf(pdf_b64))
        except PdfError as exc:
            return jsonify({'error': str(exc)}), 400
    if not isinstance(text, str) or not text.strip():
        return jsonify({'error': 'csv text or a PDF is required'}), 400
    if len(text) > MAX_CHARS:
        return jsonify({'error': 'That file is too large (1 MB max)'}), 413

    parsed = parse_statement(text)
    if parsed['error']:
        return jsonify({'error': parsed['error']}), 400

    existing = {(e.created_at.date().isoformat(), round(e.amount, 2), (e.description or '').strip())
                for e in Expense.query.filter_by(user_id=user_id).all() if e.created_at}
    rows, dupes = [], 0
    for r in parsed['rows']:
        key = (r['date'], r['amount'], r['description'].strip())
        if key in existing:
            dupes += 1
            continue
        existing.add(key)
        r['category'] = rule_category(user_id, r['store_name'], r['description']) or predict_category(r['description'], r['store_name'])['category']
        rows.append(r)

    if data.get('commit') is True:
        for r in rows:
            db.session.add(Expense(
                user_id=user_id, amount=r['amount'], category=r['category'], description=r['description'],
                store_name=r['store_name'], created_at=datetime.fromisoformat(r['date']) .replace(hour=12)))
        db.session.commit()
        return jsonify({'imported': len(rows), 'duplicates': dupes, 'skipped': parsed['skipped']}), 201

    return jsonify({'rows': rows, 'duplicates': dupes, 'skipped': parsed['skipped'],
                    'total': round(sum(r['amount'] for r in rows), 2)}), 200
