"""GET /api/digest/weekly - last 7 days vs the 7 days before (free for everyone).

Renewal names are a Pro detail (same rule as /api/subscriptions); free users see how many are due.
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Expense, User
from plans import has_feature
from ml.digest import build_digest
from ml.subscription_detector import detect_subscriptions

digest_bp = Blueprint('digest', __name__)


@digest_bp.route('/digest/weekly', methods=['GET'])
@jwt_required()
def weekly_digest():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).all()
    digest = build_digest(expenses, detect_subscriptions(expenses))
    locked = not has_feature(User.query.get(user_id), 'subscription_details')
    digest['renewals_locked'] = locked
    digest['renewals_count'] = len(digest['upcoming_renewals'])
    if locked:
        digest['upcoming_renewals'] = []
    return jsonify(digest), 200
