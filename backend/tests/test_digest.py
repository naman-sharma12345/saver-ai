from datetime import date, datetime, timedelta
from types import SimpleNamespace as NS

from ml.digest import build_digest

TODAY = date(2026, 10, 9)


def _e(amount, days_ago, cat='Food', store='Cafe'):
    d = TODAY - timedelta(days=days_ago)
    return NS(amount=amount, category=cat, store_name=store, description='', created_at=datetime(d.year, d.month, d.day, 12))


def test_totals_change_and_top_category():
    ex = [_e(100, 0), _e(300, 2, 'Travel', 'Uber'), _e(200, 8), _e(200, 10)]
    d = build_digest(ex, [], today=TODAY)
    assert d['total'] == 400 and d['previous_total'] == 400 and d['change_percent'] == 0.0
    assert d['top_category'] == {'name': 'Travel', 'amount': 300}
    assert d['biggest_expense']['description'] == 'Uber'
    assert len(d['daily']) == 7 and d['no_spend_days'] == 5
    assert 'same' in d['headline']


def test_down_week_and_empty_week():
    d = build_digest([_e(100, 1), _e(500, 9)], [], today=TODAY)
    assert d['change_percent'] == -80.0 and 'down' in d['headline']
    e = build_digest([], [], today=TODAY)
    assert e['total'] == 0 and e['top_category'] is None and e['biggest_expense'] is None
    assert e['no_spend_days'] == 7 and e['change_percent'] is None


def test_window_edges():
    d = build_digest([_e(50, 6), _e(70, 7)], [], today=TODAY)
    assert d['total'] == 50 and d['previous_total'] == 70


def test_upcoming_renewals_within_a_week():
    subs = [{'merchant': 'Spotify', 'amount': 119, 'next_expected': '2026-10-12T10:00:00'},
            {'merchant': 'Gym', 'amount': 999, 'next_expected': '2026-11-20T10:00:00'}]
    d = build_digest([], subs, today=TODAY)
    assert [u['merchant'] for u in d['upcoming_renewals']] == ['Spotify']


def test_endpoint(client, auth_headers):
    r = client.get('/api/digest/weekly', headers=auth_headers)
    assert r.status_code == 200
    b = r.get_json()
    assert {'headline', 'total', 'daily', 'upcoming_renewals', 'renewals_locked'} <= set(b)
    assert client.get('/api/digest/weekly').status_code == 401


def test_logging_streak():
    from ml.digest import logging_streak
    assert logging_streak([_e(10, 0), _e(10, 1), _e(10, 2), _e(10, 4)], TODAY) == 3
    assert logging_streak([_e(10, 1), _e(10, 2)], TODAY) == 2   # today not logged yet: streak still alive
    assert logging_streak([_e(10, 2)], TODAY) == 0
    assert logging_streak([], TODAY) == 0
