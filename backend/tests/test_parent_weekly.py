from app import db
from models import Expense, User


def _sid(client, auth_headers):
    return client.get('/api/auth/me', headers=auth_headers).get_json()['user']['id']


def test_parent_sees_weekly_shape_not_details(client, auth_headers, parent_headers, app):
    sid = _sid(client, auth_headers)
    with app.app_context():
        db.session.add(Expense(user_id=sid, amount=250, description='Secret thing', store_name='Secret Store', category='Shopping'))
        db.session.commit()
    r = client.get('/api/parent/children/%d/weekly' % sid, headers=parent_headers)
    assert r.status_code == 200
    d = r.get_json()
    assert d['total'] >= 250 and d['top_category'] and len(d['daily']) == 7
    assert 'biggest_expense' not in d and 'upcoming_renewals' not in d
    assert 'Secret' not in r.get_data(as_text=True)


def test_weekly_access_rules(client, auth_headers, parent_headers, app):
    sid = _sid(client, auth_headers)
    assert client.get('/api/parent/children/%d/weekly' % sid).status_code == 401
    assert client.get('/api/parent/children/%d/weekly' % sid, headers=auth_headers).status_code in (401, 403)
    with app.app_context():
        u = User(email='other2@test.com', password_hash='x', role='student', name='Other')
        db.session.add(u)
        db.session.commit()
        uid = u.id
    assert client.get('/api/parent/children/%d/weekly' % uid, headers=parent_headers).status_code == 403
    assert client.get('/api/parent/children/99999/weekly', headers=parent_headers).status_code == 404


def test_children_list_and_summary(client, auth_headers, parent_headers, app):
    sid = _sid(client, auth_headers)
    r = client.get('/api/parent/children', headers=parent_headers)
    assert r.status_code == 200 and sid in [c['id'] for c in r.get_json()['children']]
    s = client.get('/api/parent/children/%d/summary' % sid, headers=parent_headers).get_json()
    assert set(s) == {'total_spent', 'allowance', 'health_score', 'recent_anomalies'}
    assert client.get('/api/parent/children', headers=auth_headers).status_code in (401, 403)
    assert client.get('/api/parent/children/99999/summary', headers=parent_headers).status_code == 404
