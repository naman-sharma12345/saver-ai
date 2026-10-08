def test_oversized_request_is_rejected_as_json(client):
    r = client.post('/api/auth/login', data=b'x' * (7 * 1024 * 1024), content_type='application/json')
    assert r.status_code == 413 and 'too large' in r.get_json()['error']


def test_overlong_expense_fields_are_a_400_not_a_500(client, auth_headers):
    base = {'amount': 10, 'description': 'ok', 'store_name': 'ok'}
    for field, n in (('description', 256), ('store_name', 121), ('category', 51)):
        r = client.post('/api/expenses', json={**base, field: 'a' * n}, headers=auth_headers)
        assert r.status_code == 400 and field in r.get_json()['error']
    good = client.post('/api/expenses', json={**base, 'description': 'a' * 255, 'category': 'Food'}, headers=auth_headers)
    assert good.status_code == 201
    eid = good.get_json()['expense']['id']
    assert client.put(f'/api/expenses/{eid}', json={'category': 'c' * 51}, headers=auth_headers).status_code == 400
