"""GET /api/subscriptions - detected recurring charges (Pro: ai_insights)."""
from flask import Blueprint, jsonify, request
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


@subscriptions_bp.route('/subscriptions/upcoming', methods=['GET'])
@jwt_required()
def upcoming_charges():
    """Recurring charges expected in the next N days (default 14, max 60).

    Free users see how many and how much; Pro sees which ones and when.
    """
    from datetime import datetime, timedelta
    user_id = int(get_jwt_identity())
    try:
        days = max(1, min(60, int(request.args.get('days', 14))))
    except (TypeError, ValueError):
        days = 14
    now = datetime.utcnow()
    horizon = now + timedelta(days=days)
    subs = detect_subscriptions(Expense.query.filter_by(user_id=user_id).all())
    due = []
    for s in subs:
        when = datetime.fromisoformat(s['next_expected'])
        if when.tzinfo is not None:
            when = when.replace(tzinfo=None)
        # A charge a few days late is still "due"; one weeks overdue is probably cancelled.
        if now - timedelta(days=3) <= when <= horizon:
            due.append({'merchant': s['merchant'], 'amount': s['amount'], 'period': s['period'], 'due_on': when.date().isoformat()})
    due.sort(key=lambda d: d['due_on'])
    locked = not has_feature(User.query.get(user_id), 'subscription_details')
    return jsonify({
        'locked': locked,
        'days': days,
        'count': len(due),
        'total': round(sum(d['amount'] for d in due), 2),
        'items': [] if locked else due,
    }), 200
