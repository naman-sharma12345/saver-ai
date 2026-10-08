from ml.whatif import simulate

SPEND = {'Food': 3000.0, 'Entertainment': 1000.0, 'Bills': 500.0}
GOALS = [{'name': 'Laptop', 'target_amount': 60000, 'saved_amount': 12000}]


def test_savings_and_goal_months():
    r = simulate(SPEND, {'Food': 20, 'Entertainment': 50}, GOALS)
    assert r['monthly_saving'] == 1100 and r['yearly_saving'] == 13200
    assert r['goal'] == {'name': 'Laptop', 'remaining': 48000, 'months': 44}
    assert [c['category'] for c in r['categories']] == ['Food', 'Entertainment', 'Bills']


def test_no_cuts_and_bad_input():
    r = simulate(SPEND, {}, GOALS)
    assert r['monthly_saving'] == 0 and r['goal']['months'] is None
    r = simulate(SPEND, {'Food': 500, 'Bills': -5, 'Entertainment': 'x'}, [])
    assert r['monthly_saving'] == 3000 and r['goal'] is None   # capped at 100%, negatives ignored


def test_finished_goal_is_skipped():
    done = [{'name': 'Phone', 'target_amount': 100, 'saved_amount': 100}] + GOALS
    assert simulate(SPEND, {'Food': 10}, done)['goal']['name'] == 'Laptop'


def test_endpoint(client, auth_headers):
    client.post('/api/expenses', json={'amount': 1000, 'category': 'Food', 'description': 'meals', 'store_name': 'Mess'}, headers=auth_headers)
    r = client.post('/api/whatif', json={'cuts': {'Food': 10}}, headers=auth_headers)
    body = r.get_json()
    assert r.status_code == 200 and body['monthly_saving'] >= 100
    assert client.post('/api/whatif', json={'cuts': 5}, headers=auth_headers).status_code == 400
    assert client.post('/api/whatif', json={}).status_code == 401
