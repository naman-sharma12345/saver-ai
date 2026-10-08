from datetime import datetime, timedelta
from types import SimpleNamespace as NS

from ml.subscription_detector import detect_subscriptions, normalize_merchant


def _e(store, amount, days_ago):
    return NS(store_name=store, description='', amount=amount, created_at=datetime(2026, 10, 1) - timedelta(days=days_ago))


def test_normalize():
    assert normalize_merchant('Spotify Premium 199') == 'spotify'


def test_detects_monthly_subscription():
    ex = [_e('Spotify', 119, d) for d in (0, 30, 61, 91)]
    subs = detect_subscriptions(ex)
    assert len(subs) == 1 and subs[0]['period'] == 'monthly' and subs[0]['merchant'] == 'Spotify'
    assert subs[0]['annual_cost'] == round(119 * 12, 2)


def test_ignores_irregular_spending():
    ex = [_e('Dominos', a, d) for a, d in [(450, 1), (230, 4), (780, 19), (320, 22), (610, 40)]]
    assert detect_subscriptions(ex) == []


def test_single_charge_is_not_a_subscription():
    assert detect_subscriptions([_e('Netflix', 199, 3)]) == []


def test_two_charges_a_week_apart_is_not_weekly():
    assert detect_subscriptions([_e('Uber', 420, 1), _e('Uber', 250, 8)]) == []


def test_three_weekly_charges_are_detected():
    ex = [_e('Milk Delivery', 140, d) for d in (0, 7, 14, 21)]
    subs = detect_subscriptions(ex)
    assert len(subs) == 1 and subs[0]['period'] == 'weekly'


def test_subscriptions_endpoint(client, auth_headers):
    r = client.get('/api/subscriptions', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert 'subscriptions' in body and 'total_monthly' in body
