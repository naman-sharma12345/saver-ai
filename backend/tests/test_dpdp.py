from datetime import date

from routes.auth import _age


def _reg(client, email, **kw):
    body = {'email': email, 'password': 'secret123', 'name': 'Kid', 'accept_terms': True}
    body.update(kw)
    return client.post('/api/auth/register', json=body)


def _years_ago(n):
    t = date.today()
    return date(t.year - n, 1, 1).isoformat()


def test_age_math():
    assert _age(date(2008, 10, 10), today=date(2026, 10, 9)) == 17
    assert _age(date(2008, 10, 9), today=date(2026, 10, 9)) == 18


def test_terms_and_dob_required(client):
    assert _reg(client, 'a1@t.com', date_of_birth=_years_ago(20), accept_terms=False).status_code == 400
    assert _reg(client, 'a2@t.com').status_code == 400
    assert _reg(client, 'a3@t.com', date_of_birth='2999-01-01').status_code == 400
    assert _reg(client, 'a4@t.com', date_of_birth=_years_ago(3)).status_code == 400


def test_adult_gets_tokens(client):
    r = _reg(client, 'adult@t.com', date_of_birth=_years_ago(20))
    assert r.status_code == 201 and 'access_token' in r.get_json()


def test_minor_needs_guardian_email(client):
    assert _reg(client, 'm1@t.com', date_of_birth=_years_ago(15)).status_code == 400
    assert _reg(client, 'm1@t.com', date_of_birth=_years_ago(15), guardian_email='m1@t.com').status_code == 400


def test_minor_flow_approve(client):
    r = _reg(client, 'minor@t.com', date_of_birth=_years_ago(15), guardian_email='mom@t.com')
    body = r.get_json()
    assert r.status_code == 202 and body['consent_required'] and 'access_token' not in body
    token = body['dev_token']
    login = client.post('/api/auth/login', json={'email': 'minor@t.com', 'password': 'secret123'})
    assert login.status_code == 403 and login.get_json()['code'] == 'consent_pending'
    assert client.get('/api/auth/guardian-consent?token=' + token).get_json()['name'] == 'Kid'
    assert client.post('/api/auth/guardian-consent', json={'token': token, 'approve': True}).status_code == 200
    assert client.post('/api/auth/login', json={'email': 'minor@t.com', 'password': 'secret123'}).status_code == 200
    # single use
    assert client.post('/api/auth/guardian-consent', json={'token': token, 'approve': True}).status_code == 400


def test_minor_flow_decline_deletes_account(client):
    token = _reg(client, 'minor2@t.com', date_of_birth=_years_ago(14), guardian_email='dad@t.com').get_json()['dev_token']
    assert client.post('/api/auth/guardian-consent', json={'token': token, 'approve': False}).status_code == 200
    assert client.post('/api/auth/login', json={'email': 'minor2@t.com', 'password': 'secret123'}).status_code == 401


def test_bad_guardian_token(client):
    assert client.post('/api/auth/guardian-consent', json={'token': 'junk', 'approve': True}).status_code == 400


def test_export_and_delete_account(client):
    t = _reg(client, 'bye@t.com', date_of_birth=_years_ago(22)).get_json()['access_token']
    h = {'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'}
    assert client.get('/api/auth/export', headers=h).get_json()['profile']['email'] == 'bye@t.com'
    assert client.delete('/api/auth/me', json={'password': 'wrong'}, headers=h).status_code == 403
    assert client.delete('/api/auth/me', json={'password': 'secret123'}, headers=h).status_code == 200
    assert client.post('/api/auth/login', json={'email': 'bye@t.com', 'password': 'secret123'}).status_code == 401
