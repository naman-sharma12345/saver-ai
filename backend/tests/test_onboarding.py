from app import db
from models import Expense, Goal, User
from tests.test_billing import _register, _auth


def test_checklist_progress(client, app):
    b = _register(client, 'onb1@test.com')
    h = _auth(b['access_token'])
    r = client.get('/api/onboarding', headers=h).get_json()
    assert r['total'] == 4 and r['complete'] is False
    assert [s['key'] for s in r['steps'] if s['done']] in ([], ['allowance'])
    with app.app_context():
        uid = User.query.filter_by(email='onb1@test.com').first().id
        db.session.add(Expense(user_id=uid, amount=50, description='Tea', category='Food'))
        db.session.add(Goal(user_id=uid, name='Phone', target_amount=1000))
        db.session.commit()
    r2 = client.get('/api/onboarding', headers=h).get_json()
    done = {s['key'] for s in r2['steps'] if s['done']}
    assert {'expense', 'goal'} <= done and r2['done'] > r['done']


def test_requires_auth(client):
    assert client.get('/api/onboarding').status_code == 401
