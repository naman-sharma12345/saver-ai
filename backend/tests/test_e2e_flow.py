"""One walk through the whole product, the way a real family would use it.

signup -> expense -> budget -> goal -> parent links and matches -> extra-money request ->
streak/ask/digest -> billing (mock mode) -> export -> delete account.
"""
from datetime import date

DOB = '2002-05-01'


def _h(token):
    return {'Authorization': f'Bearer {token}'}


def _signup(client, email, role, name):
    r = client.post('/api/auth/register', json={'email': email, 'password': 'secret123', 'name': name,
                                                'role': role, 'date_of_birth': DOB, 'accept_terms': True})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['access_token']


def test_whole_product_flow(client):
    student = _signup(client, 'e2e.student@t.com', 'student', 'Asha')
    parent = _signup(client, 'e2e.parent@t.com', 'parent', 'Mr Rao')
    hs, hp = _h(student), _h(parent)

    # student sets an allowance and logs spending
    assert client.put('/api/profile', json={'monthly_allowance': 8000}, headers=hs).status_code == 200
    for amount, desc, store in [(120, 'Lunch', 'Canteen'), (60, 'Metro ride', 'Metro'), (299, 'Movie', 'PVR')]:
        r = client.post('/api/expenses', json={'amount': amount, 'description': desc, 'store_name': store}, headers=hs)
        assert r.status_code == 201, r.get_json()
    listed = client.get('/api/expenses', headers=hs).get_json()
    assert len(listed['expenses']) == 3

    # budget
    month = date.today().strftime('%Y-%m')
    r = client.post('/api/budgets', json={'category': 'Food', 'budget_limit': 2000, 'month': month}, headers=hs)
    assert r.status_code == 201, r.get_json()
    assert client.get('/api/budgets', headers=hs).status_code == 200

    # goal
    g = client.post('/api/goals', json={'name': 'Headphones', 'target_amount': 3000}, headers=hs).get_json()
    assert client.post(f"/api/goals/{g['id']}/contribute", json={'amount': 500}, headers=hs).status_code == 200

    # parent links the student and adds a match
    assert client.post('/api/parent/link', json={'student_email': 'e2e.student@t.com'}, headers=hp).status_code == 200
    kids = client.get('/api/parent/children', headers=hp).get_json()
    sid = (kids['children'] if isinstance(kids, dict) else kids)[0]['id']
    assert client.get(f'/api/parent/children/{sid}/summary', headers=hp).status_code == 200
    assert client.get(f'/api/parent/children/{sid}/weekly', headers=hp).status_code == 200
    r = client.put(f"/api/parent/children/{sid}/goals/{g['id']}/match", json={'percent': 50}, headers=hp)
    assert r.status_code == 200, r.get_json()

    # extra-money request from the student, approved by the parent
    r = client.post('/api/requests', json={'amount': 500, 'reason': 'Books'}, headers=hs)
    assert r.status_code == 201, r.get_json()
    pending = client.get('/api/requests', headers=hp).get_json()
    assert pending['pending'] == 1
    rid = pending['requests'][0]['id']
    assert client.post(f'/api/requests/{rid}/decision', json={'decision': 'approve'}, headers=hp).status_code == 200
    assert client.get('/api/requests', headers=hs).get_json()['requests'][0]['status'] == 'approved'

    # habit and insight endpoints work for a normal user
    streak = client.get('/api/streak', headers=hs).get_json()
    assert streak['current'] >= 1 and streak['logged_today'] is True
    ask = client.post('/api/ask', json={'question': 'how much did I spend this month?'}, headers=hs)
    assert ask.status_code == 200 and '479' in ask.get_json()['answer'].replace(',', '')
    assert client.get('/api/digest/weekly', headers=hs).status_code == 200
    assert client.get('/api/onboarding', headers=hs).status_code == 200

    # billing in mock mode: trial user upgrades, then cancels
    status = client.get('/api/billing/status', headers=hs).get_json()
    assert status['entitlement']['is_pro'] is True
    r = client.post('/api/billing/checkout', json={'interval': 'monthly'}, headers=hs)
    assert r.status_code == 200, r.get_json()
    assert client.post('/api/billing/cancel', headers=hs).status_code == 200

    # privacy: export has the data, delete removes the account
    export = client.get('/api/auth/export', headers=hs)
    assert export.status_code == 200 and 'Lunch' in export.get_data(as_text=True)
    assert client.delete('/api/auth/me', json={'password': 'secret123'}, headers=hs).status_code == 200
    assert client.post('/api/auth/login', json={'email': 'e2e.student@t.com', 'password': 'secret123'}).status_code == 401
