from app import db
from models import User


def _student_id(client, auth_headers):
    return client.get('/api/auth/me', headers=auth_headers).get_json()['user']['id']


def test_parent_can_remind_linked_student(client, auth_headers, parent_headers, app):
    sid = _student_id(client, auth_headers)
    r = client.post('/api/parent/children/%d/remind' % sid, json={'note': 'Remember the budget'}, headers=parent_headers)
    assert r.status_code == 200 and 'Reminder sent' in r.get_json()['message']


def test_remind_rejects_long_note_and_students(client, auth_headers, parent_headers):
    sid = _student_id(client, auth_headers)
    assert client.post('/api/parent/children/%d/remind' % sid, json={'note': 'x' * 200}, headers=parent_headers).status_code == 400
    assert client.post('/api/parent/children/%d/remind' % sid, json={}, headers=auth_headers).status_code in (401, 403)
    assert client.post('/api/parent/children/%d/remind' % sid, json={}).status_code == 401


def test_remind_unlinked_student_forbidden(client, parent_headers, app):
    with app.app_context():
        u = User(email='other@test.com', password_hash='x', role='student', name='Other')
        db.session.add(u)
        db.session.commit()
        uid = u.id
    assert client.post('/api/parent/children/%d/remind' % uid, json={}, headers=parent_headers).status_code == 403
    assert client.post('/api/parent/children/99999/remind', json={}, headers=parent_headers).status_code == 404
