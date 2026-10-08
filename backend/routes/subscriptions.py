"""GET /api/subscriptions - detected recurring charges (Pro: ai_insights)."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Expense
from models import User
from plans import has_feature
from ml.subscription_detector import detect_subscriptions

subscriptions_bp = Blueprint('subscriptions', __name__)


@subscriptions_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
def list_subscriptions():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).all()
    subs = detect_subscriptions(expenses)
    # Free plan sees the headline (how many and how much), Pro sees which ones.
    locked = not has_feature(User.query.get(user_id), 'subscription_details')
    return jsonify({
        'locked': locked,
        'count': len(subs),
        'subscriptions': [] if locked else subs,
        'total_monthly': round(sum(s['monthly_cost'] for s in subs), 2),
        'total_annual': round(sum(s['annual_cost'] for s in subs), 2),
    }), 200
