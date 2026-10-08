"""
Plans, trial and entitlements.

Single place that decides what a user may use. Keep the prices/feature copy in
frontend/src/config/plans.ts in sync with this file.
"""
from datetime import datetime, timedelta
from functools import wraps

from flask import current_app, jsonify
from flask_jwt_extended import get_jwt_identity

# Free forever: the daily-habit core (tracking, budgets, runway, health score, alerts, 1 tip a day,
# subscription headline). Pro: the depth (every tip, ML forecast, store finder, details, parent link).
PRO_FEATURES = frozenset({'all_tips', 'forecast', 'store_alternatives', 'parent_link', 'subscription_details'})
FREE_FEATURES = frozenset({'expenses', 'budgets', 'basic_analytics', 'health_score', 'anomaly_alerts', 'daily_tip', 'subscription_summary'})

PLAN_PRICES_INR = {'monthly': 79, 'yearly': 599}  # placeholders, validate with real users


def utcnow():
    return datetime.utcnow()


def trial_days():
    try:
        return int(current_app.config.get('TRIAL_DAYS', 7))
    except RuntimeError:
        return 7


def start_trial_end(now=None):
    return (now or utcnow()) + timedelta(days=trial_days())


def get_entitlement(user, now=None):
    """Return the user's current entitlement as a plain dict (safe to send to the client)."""
    now = now or utcnow()
    if user.plan == 'pro' and (user.plan_expires_at is None or user.plan_expires_at > now):
        return {
            'status': 'active', 'plan': 'pro', 'is_pro': True,
            'trial_ends_at': user.trial_ends_at.isoformat() if user.trial_ends_at else None,
            'trial_days_left': 0,
            'plan_expires_at': user.plan_expires_at.isoformat() if user.plan_expires_at else None,
            'features': sorted(PRO_FEATURES | FREE_FEATURES),
        }
    if user.trial_ends_at and user.trial_ends_at > now:
        days_left = max(1, (user.trial_ends_at - now).days + (1 if (user.trial_ends_at - now).seconds else 0))
        return {
            'status': 'trial', 'plan': 'pro', 'is_pro': True,
            'trial_ends_at': user.trial_ends_at.isoformat(), 'trial_days_left': days_left,
            'plan_expires_at': None,
            'features': sorted(PRO_FEATURES | FREE_FEATURES),
        }
    return {
        'status': 'expired' if user.trial_ends_at or user.plan == 'pro' else 'free',
        'plan': 'free', 'is_pro': False,
        'trial_ends_at': user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        'trial_days_left': 0,
        'plan_expires_at': user.plan_expires_at.isoformat() if user.plan_expires_at else None,
        'features': sorted(FREE_FEATURES),
    }


def has_feature(user, feature):
    return feature in get_entitlement(user)['features']


def require_feature(feature):
    """Decorator for routes (place under @jwt_required()). Returns 402 when the plan lacks the feature."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from models import User
            user = User.query.get(int(get_jwt_identity()))
            if user is None:
                return jsonify({'error': 'User not found'}), 404
            if not has_feature(user, feature):
                return jsonify({
                    'error': 'This feature is part of SaverAI Pro.',
                    'code': 'upgrade_required',
                    'feature': feature,
                    'entitlement': get_entitlement(user),
                }), 402
            return fn(*args, **kwargs)
        return wrapper
    return deco
