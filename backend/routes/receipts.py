"""POST /api/expenses/receipt - read a receipt photo with local OCR and suggest an expense.

Body: {"image_base64": "<image bytes, base64>"}. Nothing is saved; the user confirms
the suggestion in the normal add-expense flow. Runs the Tesseract binary on the server.
"""
import base64
import binascii

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ml.categorizer import predict_category
from ml.category_rules import rule_category
from ml.ocr import OcrError, OcrUnavailable, image_to_text, MAX_BYTES
from ml.receipt_parser import parse_receipt
from utils.ratelimit import rate_limit

receipts_bp = Blueprint('receipts', __name__)


@receipts_bp.route('/expenses/receipt', methods=['POST'])
@jwt_required()
@rate_limit('receipt', 20, 600)
def scan_receipt():
    user_id = int(get_jwt_identity())
    b64 = (request.get_json(silent=True) or {}).get('image_base64')
    if not isinstance(b64, str) or not b64:
        return jsonify({'error': 'image_base64 is required'}), 400
    if len(b64) > MAX_BYTES * 4 // 3 + 16:
        return jsonify({'error': 'That image is too large (5 MB max)'}), 413
    try:
        data = base64.b64decode(b64.split(',', 1)[-1], validate=True)
    except (binascii.Error, ValueError):
        return jsonify({'error': 'image_base64 is not valid base64'}), 400
    try:
        text = image_to_text(data)
    except OcrUnavailable as exc:
        return jsonify({'error': str(exc)}), 503
    except OcrError as exc:
        return jsonify({'error': str(exc)}), 400
    parsed = parse_receipt(text)
    if parsed['found'] == 0:
        return jsonify({'error': 'Could not find a total, merchant or date. Try a sharper, well-lit photo.'}), 422
    desc = parsed['merchant'] or ''
    parsed['category'] = (rule_category(user_id, desc, desc) or predict_category(desc, desc)['category']) if desc else None
    return jsonify(parsed), 200
