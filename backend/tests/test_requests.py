from tests.test_billing import _register, _auth


def test_request_flow(client, auth_headers, parent_headers):
    r = client.post('/api/requests', json={'amount': 1500, 'reason': 'Books for exams'}, headers=auth_headers)
    assert r.status_code == 201 and r.get_json()['status'] == 'pending'
    rid = r.get_json()['id']
    # one pending at a time
    assert client.post('/api/requests', json={'amount': 10, 'reason': 'x'}, headers=auth_headers).status_code == 409
    mine = client.get('/api/requests', headers=parent_headers).get_json()
    assert mine['pending'] >= 1 and any(q['id'] == rid for q in mine['requests'])
    d = client.post('/api/requests/%d/decision' % rid, json={'decision': 'approve', 'note': 'ok'}, headers=parent_headers)
    assert d.status_code == 200 and d.get_json()['status'] == 'approved'
    assert client.post('/api/requests/%d/decision' % rid, json={'decision': 'decline'}, headers=parent_headers).status_code == 409
    own = client.get('/api/requests', headers=auth_headers).get_json()
    assert own['pending'] == 0 and own['requests'][0]['parent_note'] == 'ok'


def test_validation_and_roles(client, auth_headers, parent_headers):
    for bad in ({'amount': 0, 'reason': 'x'}, {'amount': -5, 'reason': 'x'}, {'amount': 'a', 'reason': 'x'},
                {'amount': True, 'reason': 'x'}, {'amount': 100, 'reason': ''}, {'amount': 100, 'reason': 'x' * 200},
                {'amount': 10 ** 7, 'reason': 'x'}):
        assert client.post('/api/requests', json=bad, headers=auth_headers).status_code == 400
    assert client.post('/api/requests', json={'amount': 5, 'reason': 'x'}, headers=parent_headers).status_code == 403
    assert client.post('/api/requests', json={'amount': 5, 'reason': 'x'}).status_code == 401


def test_unlinked_student_and_foreign_parent(client, parent_headers):
    b = _register(client, 'req-solo@test.com')
    r = client.post('/api/requests', json={'amount': 50, 'reason': 'x'}, headers=_auth(b['access_token']))
    assert r.status_code == 400
    assert client.post('/api/requests/99999/decision', json={'decision': 'approve'}, headers=parent_headers).status_code == 404
    assert client.post('/api/requests/1/decision', json={'decision': 'approve'}, headers=_auth(b['access_token'])).status_code == 403


def test_bad_decision_value(client, auth_headers, parent_headers):
    rid = client.post('/api/requests', json={'amount': 20, 'reason': 'snacks'}, headers=auth_headers).get_json()['id']
    assert client.post('/api/requests/%d/decision' % rid, json={'decision': 'maybe'}, headers=parent_headers).status_code == 400
    assert client.post('/api/requests/%d/decision' % rid, json={'decision': 'decline', 'note': 'n' * 200}, headers=parent_headers).status_code == 400


def test_export_and_delete_cover_requests(client, parent_headers, app):
    from models import AllowanceRequest, User
    b = _register(client, 'req-del@test.com')
    h = _auth(b['access_token'])
    assert client.post('/api/parent/link', json={'student_email': 'req-del@test.com'}, headers=parent_headers).status_code == 200
    assert client.post('/api/requests', json={'amount': 75, 'reason': 'bus pass'}, headers=h).status_code == 201
    exp = client.get('/api/auth/export', headers=h).get_json()
    assert [r['reason'] for r in exp['allowance_requests']] == ['bus pass']
    assert client.delete('/api/auth/me', json={'password': 'secret123'}, headers=h).status_code == 200
    with app.app_context():
        assert AllowanceRequest.query.filter_by(reason='bus pass').count() == 0
