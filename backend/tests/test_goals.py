from datetime import date, datetime, timedelta
from types import SimpleNamespace as NS

from ml.goal_planner import project_goal


def _g(target, saved, days_old, deadline=None):
    return NS(target_amount=target, saved_amount=saved, deadline=deadline,
              created_at=datetime(2026, 10, 1) - timedelta(days=days_old))


TODAY = date(2026, 10, 1)


def test_projection_from_saved_pace():
    p = project_goal(_g(10000, 2000, 30), today=TODAY)
    assert p['pace_per_month'] == 2000.0 and p['pace_source'] == 'saved'
    assert p['projected_finish'] == (TODAY + timedelta(days=120)).isoformat()


def test_completed_goal():
    assert project_goal(_g(500, 600, 10), today=TODAY)['status'] == 'done'


def test_surplus_fallback_and_no_pace():
    assert project_goal(_g(3000, 0, 5), today=TODAY, monthly_surplus=1000)['pace_source'] == 'surplus'
    assert project_goal(_g(3000, 0, 5), today=TODAY)['status'] == 'no_pace'


def test_behind_deadline_and_needed_per_month():
    p = project_goal(_g(10000, 1000, 30, deadline=TODAY + timedelta(days=60)), today=TODAY)
    assert p['status'] == 'behind' and p['needed_per_month'] == 4500.0


def test_goal_crud(client, auth_headers):
    r = client.post('/api/goals', json={'name': 'Headphones', 'target_amount': 3000}, headers=auth_headers)
    assert r.status_code == 201
    gid = r.get_json()['id']
    r = client.post(f'/api/goals/{gid}/contribute', json={'amount': 500}, headers=auth_headers)
    assert r.get_json()['saved_amount'] == 500
    r = client.put(f'/api/goals/{gid}', json={'name': 'Good headphones'}, headers=auth_headers)
    assert r.get_json()['name'] == 'Good headphones'
    assert any(g['id'] == gid for g in client.get('/api/goals', headers=auth_headers).get_json()['goals'])
    assert client.delete(f'/api/goals/{gid}', headers=auth_headers).status_code == 200
    assert client.delete(f'/api/goals/{gid}', headers=auth_headers).status_code == 404


def test_goal_validation_and_privacy(client, auth_headers, parent_headers):
    assert client.post('/api/goals', json={'name': '', 'target_amount': 10}, headers=auth_headers).status_code == 400
    assert client.post('/api/goals', json={'name': 'x', 'target_amount': -5}, headers=auth_headers).status_code == 400
    assert client.post('/api/goals', json={'name': 'x', 'target_amount': 10, 'deadline': '2001-01-01'}, headers=auth_headers).status_code == 400
    gid = client.post('/api/goals', json={'name': 'Mine', 'target_amount': 100}, headers=auth_headers).get_json()['id']
    assert client.delete(f'/api/goals/{gid}', headers=parent_headers).status_code == 404
    assert client.get('/api/goals').status_code == 401
