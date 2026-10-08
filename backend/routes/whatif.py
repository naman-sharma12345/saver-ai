"""POST /api/whatif - "what if I spent X% less on Food?" Free for everyone.

Body: {"cuts": {"Food": 20, "Entertainment": 50}}. An empty body returns the baseline.
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from models import db, Expense, Goal
from ml.whatif import simulate

whatif_bp = Blueprint('whatif', __name__)


@whatif_bp.route('/whatif', methods=['POST'])
@jwt_required()
def whatif():
    user_id = int(get_jwt_identity())
    cuts = (request.get_json(silent=True) or {}).get('cuts') or {}
    if not isinstance(cuts, dict):
        return jsonify({'error': 'cuts must be an object like {"Food": 20}'}), 400
    since = datetime.utcnow() - timedelta(days=30)
    rows = db.session.query(Expense.category, func.sum(Expense.amount)).filter(
        Expense.user_id == user_id, Expense.created_at >= since).group_by(Expense.category).all()
    goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.deadline.is_(None), Goal.deadline, Goal.id).all()
    return jsonify(simulate({c or 'Other': float(t or 0) for c, t in rows}, cuts,
                            [{'name': g.name, 'target_amount': g.target_amount, 'saved_amount': g.saved_amount}
                             for g in goals])), 200
