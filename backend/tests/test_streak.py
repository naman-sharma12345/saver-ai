import types
from datetime import date, datetime, timedelta

from ml.streaks import streak_summary

T = date(2026, 10, 14)


def _e(*ago):
    return [types.SimpleNamespace(created_at=datetime.combine(T - timedelta(days=a), datetime.min.time())) for a in ago]


def test_streak_math():
    s = streak_summary(_e(0, 1, 2, 5, 6, 7, 8, 9), T)
    assert s['current'] == 3 and s['best'] == 5 and s['logged_today'] is True
    assert [b['earned'] for b in s['badges']][:2] == [True, False]
    assert s['next_milestone'] == {'days': 7, 'name': 'One week', 'to_go': 4}


def test_streak_survives_until_end_of_today():
    s = streak_summary(_e(1, 2, 3), T)
    assert s['current'] == 3 and s['logged_today'] is False
    assert streak_summary(_e(2, 3), T)['current'] == 0
    assert streak_summary([], T)['best'] == 0


def test_future_dates_ignored_and_endpoint(client, auth_headers):
    assert streak_summary(_e(-3, -2), T)['best'] == 0
    r = client.get('/api/streak', headers=auth_headers)
    assert r.status_code == 200 and {'current', 'best', 'badges'} <= set(r.get_json())
    assert client.get('/api/streak').status_code == 401
