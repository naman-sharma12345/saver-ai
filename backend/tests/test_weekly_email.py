from models import User
from utils.weekly_email import compose, send_weekly_parent_emails


def test_opt_in_and_preview(client, auth_headers, parent_headers):
    assert client.get('/api/parent/weekly-email', headers=parent_headers).get_json()['enabled'] is False
    assert client.put('/api/parent/weekly-email', json={'enabled': 'yes'}, headers=parent_headers).status_code == 400
    assert client.put('/api/parent/weekly-email', json={'enabled': True}, headers=parent_headers).get_json()['enabled'] is True
    r = client.post('/api/parent/weekly-email/preview', headers=parent_headers)
    assert r.status_code == 200
    # students cannot use the parent endpoints
    assert client.get('/api/parent/weekly-email', headers=auth_headers).status_code == 403
    assert client.get('/api/parent/weekly-email').status_code == 401


def test_compose_and_send(app, client, parent_headers):
    client.put('/api/parent/weekly-email', json={'enabled': True}, headers=parent_headers)
    with app.app_context():
        parent = User.query.filter_by(role='parent', weekly_email=True).first()
        subject, body = compose(parent)
        assert 'weekly' in subject.lower() and 'no-spend' in body
        assert send_weekly_parent_emails() >= 1
