from ml.category_rules import merchant_key


def _new(client, h, store, desc, **kw):
    r = client.post('/api/expenses', json={'amount': 100, 'description': desc, 'store_name': store, **kw}, headers=h)
    assert r.status_code == 201, r.get_json()
    return r.get_json()


def test_merchant_key_normalises():
    assert merchant_key('Zomato 4023!') == 'zomato'
    assert merchant_key('', 'Chai Point #12') == 'chai point'
    assert merchant_key('', '') == ''


def test_fixing_a_category_teaches_a_rule(client, auth_headers):
    first = _new(client, auth_headers, 'Blue Tokai', 'coffee beans')
    eid = first['expense']['id']
    r = client.put(f'/api/expenses/{eid}', json={'category': 'Study Materials'}, headers=auth_headers)
    assert r.status_code == 200 and r.get_json()['rule_learned'] == {'merchant': 'blue tokai', 'category': 'Study Materials'}
    # Next expense from the same merchant uses the taught category, even with a different description
    nxt = _new(client, auth_headers, 'Blue Tokai', 'latte')
    assert nxt['expense']['category'] == 'Study Materials' and nxt['categorization']['method'] == 'your_rule'
    # An explicit category still wins
    explicit = _new(client, auth_headers, 'Blue Tokai', 'snack', category='Food')
    assert explicit['expense']['category'] == 'Food'


def test_unchanged_category_learns_nothing_and_rules_can_be_removed(client, auth_headers):
    e = _new(client, auth_headers, 'Local Tailor', 'stitching')
    same = client.put(f"/api/expenses/{e['expense']['id']}", json={'category': e['expense']['category']}, headers=auth_headers)
    assert 'rule_learned' not in same.get_json()
    client.put(f"/api/expenses/{e['expense']['id']}", json={'category': 'Other'}, headers=auth_headers)
    rules = client.get('/api/category-rules', headers=auth_headers).get_json()['rules']
    mine = [r for r in rules if r['merchant'] == 'local tailor']
    assert len(mine) == 1
    assert client.delete(f"/api/category-rules/{mine[0]['id']}", headers=auth_headers).status_code == 200
    assert client.delete(f"/api/category-rules/{mine[0]['id']}", headers=auth_headers).status_code == 404
    assert client.get('/api/category-rules').status_code == 401


def test_rules_are_per_user(app, client, auth_headers):
    from ml.category_rules import rule_category
    e = _new(client, auth_headers, 'Corner Shop Xyz', 'misc')
    client.put(f"/api/expenses/{e['expense']['id']}", json={'category': 'Health'}, headers=auth_headers)
    with app.app_context():
        from models import CategoryRule
        owner = CategoryRule.query.filter_by(merchant_key='corner shop xyz').first().user_id
        assert rule_category(owner, 'Corner Shop Xyz') == 'Health'
        assert rule_category(owner + 1000, 'Corner Shop Xyz') is None
