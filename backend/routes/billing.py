"""
Billing routes.

Mock mode (default, no Razorpay keys): checkout "succeeds" instantly in dev/test so the
whole paywall flow can be exercised. Live mode (RAZORPAY_KEY_ID/SECRET set): creates a
Razorpay subscription and waits for the signed webhook to activate Pro.

TODO(razorpay): once keys exist, set RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET,
RAZORPAY_WEBHOOK_SECRET, RAZORPAY_PLAN_ID_MONTHLY / _YEARLY in backend/.env and point the
Razorpay dashboard webhook at POST /api/billing/webhook (events: subscription.activated,
subscription.charged, subscription.cancelled, subscription.halted, subscription.completed).
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta

import requests
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import User
from plans import PLAN_PRICES_INR, get_entitlement, trial_days, utcnow

billing_bp = Blueprint('billing', __name__)

PERIOD_DAYS = {'monthly': 31, 'yearly': 366}


def live_mode():
    cfg = current_app.config
    return bool(cfg.get('RAZORPAY_KEY_ID') and cfg.get('RAZORPAY_KEY_SECRET'))


def _current_user():
    return User.query.get(int(get_jwt_identity()))


@billing_bp.route('/status', methods=['GET'])
@jwt_required()
def status():
    user = _current_user()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'entitlement': get_entitlement(user),
        'mode': 'live' if live_mode() else 'mock',
        'prices_inr': PLAN_PRICES_INR,
        'trial_days': trial_days(),
    }), 200


@billing_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Start a Pro subscription. Body: {"interval": "monthly" | "yearly"}."""
    user = _current_user()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json(silent=True) or {}
    interval = data.get('interval', 'monthly')
    if interval not in PERIOD_DAYS:
        return jsonify({'error': "interval must be 'monthly' or 'yearly'"}), 400

    if not live_mode():
        # Mock mode: never available in production.
        if current_app.config.get('IS_PRODUCTION'):
            return jsonify({'error': 'Payments are not configured'}), 503
        user.plan = 'pro'
        user.plan_expires_at = utcnow() + timedelta(days=PERIOD_DAYS[interval])
        user.billing_ref = 'mock_sub_%d' % user.id
        db.session.commit()
        return jsonify({'mode': 'mock', 'message': 'Pro activated (mock mode, no charge).',
                        'entitlement': get_entitlement(user)}), 200

    cfg = current_app.config
    plan_id = cfg['RAZORPAY_PLAN_ID_YEARLY'] if interval == 'yearly' else cfg['RAZORPAY_PLAN_ID_MONTHLY']
    if not plan_id:
        return jsonify({'error': 'Razorpay plan id is not configured for this interval'}), 503
    try:
        resp = requests.post(
            'https://api.razorpay.com/v1/subscriptions',
            auth=(cfg['RAZORPAY_KEY_ID'], cfg['RAZORPAY_KEY_SECRET']),
            json={'plan_id': plan_id, 'total_count': 120 if interval == 'monthly' else 10,
                  'customer_notify': 1, 'notes': {'user_id': str(user.id)}},
            timeout=15,
        )
        resp.raise_for_status()
        sub = resp.json()
    except requests.RequestException as exc:
        current_app.logger.error('Razorpay subscription create failed: %s', exc)
        return jsonify({'error': 'Could not start checkout. Please try again.'}), 502
    user.billing_ref = sub.get('id')
    db.session.commit()
    # The client opens Razorpay Checkout with key_id + subscription_id; Pro is activated by the webhook.
    return jsonify({'mode': 'live', 'key_id': cfg['RAZORPAY_KEY_ID'], 'subscription_id': sub.get('id')}), 200


@billing_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel():
    """Cancel auto-renew. Pro stays until the paid period ends."""
    user = _current_user()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    if live_mode() and user.billing_ref and not user.billing_ref.startswith('mock_'):
        cfg = current_app.config
        try:
            requests.post(
                'https://api.razorpay.com/v1/subscriptions/%s/cancel' % user.billing_ref,
                auth=(cfg['RAZORPAY_KEY_ID'], cfg['RAZORPAY_KEY_SECRET']),
                json={'cancel_at_cycle_end': 1}, timeout=15,
            ).raise_for_status()
        except requests.RequestException as exc:
            current_app.logger.error('Razorpay cancel failed: %s', exc)
            return jsonify({'error': 'Could not cancel. Please try again.'}), 502
    return jsonify({'message': 'Auto-renew cancelled. Pro stays active until the end of the paid period.',
                    'entitlement': get_entitlement(user)}), 200


def verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """Razorpay webhook. Authenticated only by the HMAC signature."""
    raw = request.get_data()
    if not verify_signature(raw, request.headers.get('X-Razorpay-Signature', ''),
                            current_app.config.get('RAZORPAY_WEBHOOK_SECRET', '')):
        return jsonify({'error': 'Invalid signature'}), 400
    try:
        event = json.loads(raw)
    except ValueError:
        return jsonify({'error': 'Bad payload'}), 400

    name = event.get('event', '')
    sub = (event.get('payload', {}).get('subscription', {}) or {}).get('entity', {}) or {}
    sub_id = sub.get('id')
    user = User.query.filter_by(billing_ref=sub_id).first() if sub_id else None
    if user is None:
        return jsonify({'status': 'ignored'}), 200

    if name in ('subscription.activated', 'subscription.charged'):
        end = sub.get('current_end')
        user.plan = 'pro'
        user.plan_expires_at = (
            datetime.utcfromtimestamp(end) + timedelta(days=1) if end
            else utcnow() + timedelta(days=31)
        )
    elif name in ('subscription.cancelled', 'subscription.halted', 'subscription.completed'):
        # Keep Pro until the period already paid for ends; plan_expires_at stays as is.
        if user.plan_expires_at is None or user.plan_expires_at < utcnow():
            user.plan = 'free'
    db.session.commit()
    return jsonify({'status': 'ok'}), 200
