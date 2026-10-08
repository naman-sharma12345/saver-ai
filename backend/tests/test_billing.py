"""Tests for plans, trial, entitlement gating and billing endpoints."""
import hashlib
import hmac
import json
from datetime import datetime, timedelta

from app import db
from models import User
from plans import get_entitlement


def _register(client, email):
    r = client.post('/api/auth/register', json={'email': email, 'password': 'secret123', 'name': 'T'})
    assert r.status_code == 201
    return r.get_json()


def _auth(token):
    return {'Authorization': 'Bearer ' + token}


def test_new_user_gets_trial(client):
    body = _register(client, 'trial1@test.com')
    ent = body['user']['entitlement']
    assert ent['status'] == 'trial' and ent['is_pro'] is True
    assert 1 <= ent['trial_days_left'] <= 7
    r = client.get('/api/recommendations', headers=_auth(body['access_token']))
    assert r.status_code == 200


def test_expired_trial_is_locked(client, app):
    body = _register(client, 'expired1@test.com')
    with app.app_context():
        u = User.query.filter_by(email='expired1@test.com').first()
        u.trial_ends_at = datetime.utcnow() - timedelta(days=1)
        db.session.commit()
    h = _auth(body['access_token'])
    for method, url in [('get', '/api/recommendations'), ('get', '/api/analytics/next-month-prediction'),
                        ('post', '/api/stores/cheaper-alternatives')]:
        r = getattr(client, method)(url, headers=h)
        assert r.status_code == 402, url
        assert r.get_json()['code'] == 'upgrade_required'
    # free features still work
    assert client.get('/api/expenses', headers=h).status_code == 200


def test_mock_checkout_activates_pro(client, app):
    body = _register(client, 'buyer1@test.com')
    with app.app_context():
        u = User.query.filter_by(email='buyer1@test.com').first()
        u.trial_ends_at = datetime.utcnow() - timedelta(days=1)
        db.session.commit()
    h = _auth(body['access_token'])
    assert client.get('/api/recommendations', headers=h).status_code == 402
    r = client.post('/api/billing/checkout', json={'interval': 'monthly'}, headers=h)
    assert r.status_code == 200 and r.get_json()['mode'] == 'mock'
    assert client.get('/api/recommendations', headers=h).status_code == 200
    st = client.get('/api/billing/status', headers=h).get_json()
    assert st['entitlement']['status'] == 'active'


def test_checkout_rejects_bad_interval(client):
    body = _register(client, 'buyer2@test.com')
    r = client.post('/api/billing/checkout', json={'interval': 'weekly'}, headers=_auth(body['access_token']))
    assert r.status_code == 400


def test_webhook_requires_valid_signature(client, app):
    app.config['RAZORPAY_WEBHOOK_SECRET'] = 'whsec_test'
    payload = json.dumps({'event': 'subscription.activated',
                          'payload': {'subscription': {'entity': {'id': 'sub_X', 'current_end': 4102444800}}}}).encode()
    r = client.post('/api/billing/webhook', data=payload, headers={'X-Razorpay-Signature': 'bad'})
    assert r.status_code == 400
    r = client.post('/api/billing/webhook', data=payload)
    assert r.status_code == 400


def test_webhook_activates_user(client, app):
    secret = 'whsec_test'
    app.config['RAZORPAY_WEBHOOK_SECRET'] = secret
    _register(client, 'hook1@test.com')
    with app.app_context():
        u = User.query.filter_by(email='hook1@test.com').first()
        u.billing_ref = 'sub_HOOK1'
        u.trial_ends_at = datetime.utcnow() - timedelta(days=1)
        db.session.commit()
    payload = json.dumps({'event': 'subscription.activated',
                          'payload': {'subscription': {'entity': {'id': 'sub_HOOK1', 'current_end': 4102444800}}}}).encode()
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    r = client.post('/api/billing/webhook', data=payload, headers={'X-Razorpay-Signature': sig})
    assert r.status_code == 200
    with app.app_context():
        u = User.query.filter_by(email='hook1@test.com').first()
        assert get_entitlement(u)['status'] == 'active'


def test_no_webhook_secret_rejects_everything(client, app):
    app.config['RAZORPAY_WEBHOOK_SECRET'] = ''
    r = client.post('/api/billing/webhook', data=b'{}', headers={'X-Razorpay-Signature': ''})
    assert r.status_code == 400
