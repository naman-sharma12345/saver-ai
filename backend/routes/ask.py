"""POST /api/ask - plain-English questions about your own spending. Local ML, no LLM."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Expense, User
from plans import get_entitlement
from ml.ask_engine import answer
from utils.ratelimit import rate_limit

ask_bp = Blueprint('ask', __name__)


@ask_bp.route('/ask', methods=['POST'])
@jwt_required()
@rate_limit('ask', 60, 3600)
def ask():
    data = request.get_json(silent=True) or {}
    q = data.get('question')
    if not isinstance(q, str) or not q.strip():
        return jsonify({'error': 'question is required'}), 400
    if len(q) > 200:
        return jsonify({'error': 'Keep the question under 200 characters'}), 400
    prev = data.get('previous')
    if prev is not None and (not isinstance(prev, str) or len(prev) > 200):
        prev = None
    user = User.query.get(int(get_jwt_identity()))
    expenses = Expense.query.filter_by(user_id=user.id).all()
    return jsonify(answer(q.strip(), expenses, allowance=user.monthly_allowance or 0.0,
                          is_pro=get_entitlement(user)['is_pro'], previous=prev)), 200
