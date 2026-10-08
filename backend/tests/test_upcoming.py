"""GET /api/subscriptions/upcoming."""
from datetime import datetime, timedelta

from app import db
from models import Expense, User
from tests.test_billing import _register, _auth


def _seed(uid, last_days_ago=20):
    now = datetime.utcnow()
    for k in range(4):
        db.session.add(Expense(user_id=uid, amount=199, description='Netflix', store_name='Netflix', category='Entertainment',
                               created_at=now - timedelta(days=last_days_ago + 30 * k)))
    db.session.commit()


def test_upcoming_lists_due_charge(client, app):
    b = _register(client, 'up1@test.com')
    with app.app_context():
        _seed(User.query.filter_by(email='up1@test.com').first().id)
    r = client.get('/api/subscriptions/upcoming?days=30', headers=_auth(b['access_token'])).get_json()
    assert r['count'] == 1 and r['total'] == 199 and r['items'][0]['merchant'] == 'Netflix'


def test_upcoming_window_and_bad_param(client, app):
    b = _register(client, 'up2@test.com')
    with app.app_context():
        _seed(User.query.filter_by(email='up2@test.com').first().id, last_days_ago=1)
    h = _auth(b['access_token'])
    assert client.get('/api/subscriptions/upcoming?days=5', headers=h).get_json()['count'] == 0
    assert client.get('/api/subscriptions/upcoming?days=abc', headers=h).status_code == 200
