"""Rate limiting, password reset and email verification."""
from utils import ratelimit


def _reg(client, email, pw='secret123'):
    r = client.post('/api/auth/register', json={'email': email, 'password': pw, 'name': 'T'})
    assert r.status_code == 201
    return r.get_json()


def test_password_min_length_is_8(client):
    r = client.post('/api/auth/register', json={'email': 'short@test.com', 'password': 'abc1234', 'name': 'T'})
    assert r.status_code == 400


def test_forgot_password_does_not_reveal_accounts(client):
    r = client.post('/api/auth/forgot-password', json={'email': 'nobody@test.com'})
    assert r.status_code == 200 and 'dev_token' not in r.get_json()


def test_reset_password_flow_is_single_use(client):
    _reg(client, 'reset1@test.com')
    tok = client.post('/api/auth/forgot-password', json={'email': 'reset1@test.com'}).get_json()['dev_token']
    r = client.post('/api/auth/reset-password', json={'token': tok, 'password': 'newpass123'})
    assert r.status_code == 200
    assert client.post('/api/auth/login', json={'email': 'reset1@test.com', 'password': 'newpass123'}).status_code == 200
    assert client.post('/api/auth/login', json={'email': 'reset1@test.com', 'password': 'secret123'}).status_code == 401
    again = client.post('/api/auth/reset-password', json={'token': tok, 'password': 'another123'})
    assert again.status_code == 400


def test_reset_rejects_garbage_token(client):
    r = client.post('/api/auth/reset-password', json={'token': 'nope', 'password': 'newpass123'})
    assert r.status_code == 400


def test_email_verification_flow(client):
    body = _reg(client, 'verify1@test.com')
    assert body['user']['email_verified'] is False
    h = {'Authorization': 'Bearer ' + body['access_token']}
    tok = client.post('/api/auth/send-verification', headers=h).get_json()['dev_token']
    assert client.post('/api/auth/verify-email', json={'token': tok}).status_code == 200
    me = client.get('/api/auth/me', headers=h).get_json()['user']
    assert me['email_verified'] is True


def test_login_rate_limit(client, app):
    app.config['RATELIMIT_ENABLED'] = True
    ratelimit.reset()
    try:
        codes = [client.post('/api/auth/login', json={'email': 'x@test.com', 'password': 'wrongpass'}).status_code for _ in range(12)]
        assert codes[:10] == [401] * 10
        assert 429 in codes[10:]
    finally:
        app.config['RATELIMIT_ENABLED'] = False
        ratelimit.reset()
