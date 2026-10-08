"""API tests for auth, expense validation and access control."""

import pytest


def _json(headers):
    return {k: v for k, v in headers.items() if k != 'Content-Type'}


class TestRegister:
    def test_register_success(self, client):
        r = client.post('/api/auth/register', json={
            'email': 'New.User@Test.com', 'password': 'secret123', 'name': 'New User',
            'monthly_allowance': 5000,
        })
        assert r.status_code == 201
        body = r.get_json()
        assert body['user']['email'] == 'new.user@test.com'
        assert 'access_token' in body

    def test_register_duplicate_email(self, client):
        r = client.post('/api/auth/register', json={
            'email': 'student@test.com', 'password': 'secret123', 'name': 'Dup',
        })
        assert r.status_code == 409

    def test_register_no_body_is_400_not_500(self, client):
        assert client.post('/api/auth/register').status_code == 400
        assert client.post('/api/auth/register', data='not json',
                           content_type='application/json').status_code == 400
        assert client.post('/api/auth/register', json=['x']).status_code == 400

    @pytest.mark.parametrize('payload', [
        {'email': 'a@b.com', 'password': 'secret123'},
        {'email': 'bad-email', 'password': 'secret123', 'name': 'X'},
        {'email': 'a@b.com', 'password': '123', 'name': 'X'},
        {'email': 123, 'password': 'secret123', 'name': 'X'},
        {'email': 'a@b.com', 'password': 'secret123', 'name': 'X', 'role': 'admin'},
        {'email': 'a@b.com', 'password': 'secret123', 'name': 'X', 'monthly_allowance': -5},
        {'email': 'a@b.com', 'password': 'secret123', 'name': 'X', 'monthly_allowance': 'lots'},
    ])
    def test_register_rejects_bad_input(self, client, payload):
        assert client.post('/api/auth/register', json=payload).status_code == 400


class TestLogin:
    def test_login_success(self, client):
        r = client.post('/api/auth/login', json={'email': 'student@test.com', 'password': 'Test@123'})
        assert r.status_code == 200
        assert 'access_token' in r.get_json()

    def test_login_wrong_password(self, client):
        r = client.post('/api/auth/login', json={'email': 'student@test.com', 'password': 'nope'})
        assert r.status_code == 401

    def test_login_bad_body(self, client):
        assert client.post('/api/auth/login').status_code == 400
        assert client.post('/api/auth/login', json={'email': 1, 'password': 2}).status_code == 400

    def test_me_requires_token(self, client):
        assert client.get('/api/auth/me').status_code == 401

    def test_me_returns_profile(self, client, auth_headers):
        r = client.get('/api/auth/me', headers=_json(auth_headers))
        assert r.status_code == 200
        assert r.get_json()['user']['email'] == 'student@test.com'


class TestExpenseValidation:
    @pytest.mark.parametrize('amount', [0, -10, 'abc', None, float('inf'), True])
    def test_create_rejects_bad_amount(self, client, auth_headers, amount):
        r = client.post('/api/expenses', headers=auth_headers, json={
            'amount': amount, 'description': 'x', 'store_name': 'y',
        })
        assert r.status_code == 400

    def test_create_requires_auth(self, client):
        r = client.post('/api/expenses', json={'amount': 5, 'description': 'x', 'store_name': 'y'})
        assert r.status_code == 401

    def test_create_and_autocategorise(self, client, auth_headers):
        r = client.post('/api/expenses', headers=auth_headers, json={
            'amount': 120, 'description': 'zomato order biryani', 'store_name': 'Zomato',
        })
        assert r.status_code == 201
        assert r.get_json()['expense']['category'] == 'Food'

    def test_update_rejects_bad_amount(self, client, auth_headers):
        created = client.post('/api/expenses', headers=auth_headers, json={
            'amount': 50, 'description': 'tea', 'store_name': 'Stall', 'category': 'Food',
        }).get_json()['expense']
        for bad in (-1, 0, 'x'):
            r = client.put(f"/api/expenses/{created['id']}", headers=auth_headers, json={'amount': bad})
            assert r.status_code == 400
        r = client.put(f"/api/expenses/{created['id']}", headers=auth_headers, json={'amount': 75})
        assert r.status_code == 200
        assert r.get_json()['expense']['amount'] == 75

    def test_per_page_is_capped(self, client, auth_headers):
        r = client.get('/api/expenses?per_page=100000&page=0', headers=_json(auth_headers))
        assert r.status_code == 200
        assert r.get_json()['per_page'] <= 100
        assert r.get_json()['page'] >= 1


class TestAccessControl:
    def test_cannot_touch_other_users_expense(self, client, auth_headers, parent_headers):
        mine = client.post('/api/expenses', headers=auth_headers, json={
            'amount': 10, 'description': 'mine', 'store_name': 'S', 'category': 'Other',
        }).get_json()['expense']
        url = f"/api/expenses/{mine['id']}"
        assert client.get(url, headers=_json(parent_headers)).status_code == 404
        assert client.put(url, headers=parent_headers, json={'amount': 1}).status_code == 404
        assert client.delete(url, headers=_json(parent_headers)).status_code == 404
        assert client.get(url, headers=_json(auth_headers)).status_code == 200
        assert client.delete(url, headers=_json(auth_headers)).status_code == 200

    def test_student_cannot_retrain_model(self, client, auth_headers):
        r = client.post('/api/ml/retrain-category', headers=_json(auth_headers))
        assert r.status_code == 403

    def test_parent_is_not_admin_by_default(self, client, parent_headers):
        r = client.post('/api/ml/retrain-category', headers=_json(parent_headers))
        assert r.status_code == 403

    def test_only_listed_admin_can_retrain(self, app, client, auth_headers, parent_headers, monkeypatch):
        monkeypatch.setitem(app.config, 'ADMIN_EMAILS', ['parent@test.com'])
        monkeypatch.setattr('ml.train_category_model.train_model', lambda: object())
        monkeypatch.setattr('ml.categorizer.reload_model', lambda: None)
        assert client.post('/api/ml/retrain-category', headers=_json(auth_headers)).status_code == 403
        assert client.post('/api/ml/retrain-category', headers=_json(parent_headers)).status_code == 200
