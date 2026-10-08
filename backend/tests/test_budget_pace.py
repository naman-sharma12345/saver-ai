from datetime import date

from ml.budget_pace import budget_pace

B = [{'category': 'Food', 'budget_limit': 3000}, {'category': 'Travel', 'budget_limit': 1000},
     {'category': 'Fun', 'budget_limit': 1000}, {'category': 'Bills', 'budget_limit': 1000}]


def test_statuses_mid_month():
    r = budget_pace(B, {'Food': 2000, 'Travel': 1200, 'Fun': 500, 'Bills': 100}, today=date(2026, 9, 15))
    st = {i['category']: i['status'] for i in r['items']}
    assert st == {'Food': 'overshoot', 'Travel': 'over', 'Fun': 'tight', 'Bills': 'ok'}
    assert r['items'][0]['category'] == 'Travel'  # worst first
    food = next(i for i in r['items'] if i['category'] == 'Food')
    assert food['projected'] == 4000 and food['safe_daily'] == round(1000 / 15, 2)


def test_early_month_only_flags_already_over():
    r = budget_pace(B, {'Food': 2900, 'Travel': 1500}, today=date(2026, 9, 2))
    st = {i['category']: i['status'] for i in r['items']}
    assert st['Food'] == 'ok' and st['Travel'] == 'over'


def test_pace_endpoint(client, auth_headers):
    from datetime import datetime
    month = datetime.now().strftime('%Y-%m')
    client.post('/api/budgets', json={'category': 'Food', 'budget_limit': 500, 'month': month}, headers=auth_headers)
    client.post('/api/expenses', json={'amount': 400, 'category': 'Food', 'description': 'lunch', 'store_name': 'Cafe'}, headers=auth_headers)
    r = client.get('/api/budgets/pace', headers=auth_headers)
    body = r.get_json()
    assert r.status_code == 200 and {'day', 'days_in_month', 'items'} <= set(body)
    assert all({'category', 'limit', 'spent', 'projected', 'status'} <= set(i) for i in body['items'])
    assert client.get('/api/budgets/pace').status_code == 401
