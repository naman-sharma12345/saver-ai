def _goal(client, h):
    return client.post('/api/goals', json={'name': 'Match goal', 'target_amount': 10000}, headers=h).get_json()


def test_match_follows_savings(client, auth_headers, parent_headers):
    g = _goal(client, auth_headers)
    kids = client.get('/api/parent/children', headers=parent_headers).get_json()['children']
    assert kids, 'fixture parent should have a linked student'
    sid = kids[0]['id']
    # find the goal via the parent view of whichever child owns it
    for k in kids:
        gl = client.get('/api/parent/children/%d/goals' % k['id'], headers=parent_headers)
        if gl.status_code == 200 and any(x['id'] == g['id'] for x in gl.get_json()['goals']):
            sid = k['id']
    r = client.put('/api/parent/children/%d/goals/%d/match' % (sid, g['id']), json={'percent': 50, 'cap': 300}, headers=parent_headers)
    assert r.status_code == 200 and r.get_json()['match_percent'] == 50
    c = client.post('/api/goals/%d/contribute' % g['id'], json={'amount': 400}, headers=auth_headers).get_json()
    assert c['matched_amount'] == 200 and c['match_percent'] == 50
    c = client.post('/api/goals/%d/contribute' % g['id'], json={'amount': 400}, headers=auth_headers).get_json()
    assert c['matched_amount'] == 300  # capped
    c = client.post('/api/goals/%d/contribute' % g['id'], json={'amount': -400}, headers=auth_headers).get_json()
    assert c['matched_amount'] == 100


def test_match_validation_and_access(client, auth_headers, parent_headers):
    g = _goal(client, auth_headers)
    kids = client.get('/api/parent/children', headers=parent_headers).get_json()['children']
    for k in kids:
        for bad in ({'percent': 101}, {'percent': -1}, {'percent': 'a'}, {'percent': True}, {'percent': 10, 'cap': 0}):
            assert client.put('/api/parent/children/%d/goals/%d/match' % (k['id'], g['id']), json=bad, headers=parent_headers).status_code == 400
    # a student cannot set a match
    assert client.put('/api/parent/children/1/goals/%d/match' % g['id'], json={'percent': 10}, headers=auth_headers).status_code in (401, 403)
    assert client.put('/api/parent/children/1/goals/1/match', json={'percent': 10}).status_code == 401
