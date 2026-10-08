from datetime import date, datetime, timedelta
from types import SimpleNamespace as NS

from ml.ask_engine import answer, classify, parse_period, find_category

TODAY = date(2026, 10, 15)


def _e(store, cat, amt, days_ago):
    d = TODAY - timedelta(days=days_ago)
    return NS(store_name=store, description=store, category=cat, amount=amt, created_at=datetime(d.year, d.month, d.day, 12))


EXP = [_e('Swiggy', 'Food', 300, 2), _e('Canteen', 'Food', 100, 5), _e('Uber', 'Transport', 250, 3),
       _e('Swiggy', 'Food', 500, 20), _e('Uber', 'Transport', 200, 22), _e('Netflix', 'Entertainment', 199, 1), _e('Canteen', 'Food', 400, 40)]


def test_intents():
    assert classify('how much did I spend on food this month')[0] == 'total'
    assert classify('what was my biggest expense')[0] == 'biggest'
    assert classify('am I spending more than last month')[0] == 'compare'
    assert classify('which category do I spend most on')[0] == 'top_category'


def test_period_and_category():
    assert parse_period('spend last month', TODAY)[2] == 'last month'
    assert parse_period('in the last 10 days', TODAY)[0] == TODAY - timedelta(days=9)
    assert find_category('how much on swiggy and snacks') == 'Food'


def test_total_food_this_month():
    r = answer('how much did I spend on food this month?', EXP, today=TODAY)
    assert r['value'] == 400 and 'Rs 400' in r['answer']


def test_biggest_and_merchant():
    assert answer('biggest expense this month', EXP, today=TODAY)['value'] == 300
    assert answer('how much did I spend at Uber this month', EXP, today=TODAY)['value'] == 250


def test_compare_locked_for_free_and_open_for_pro():
    assert answer('am I spending more than last month', EXP, today=TODAY, is_pro=False)['locked'] is True
    r = answer('am I spending more than last month', EXP, today=TODAY, is_pro=True)
    assert not r['locked'] and 'value' in r


def test_left_uses_allowance():
    r = answer('how much do I have left', EXP, allowance=5000, today=TODAY)
    assert r['value'] == 5000 - (300 + 100 + 250 + 199)


def test_gibberish():
    assert answer('zzzz qqqq', EXP, today=TODAY)['intent'] == 'unknown'


def test_endpoint(client, auth_headers):
    r = client.post('/api/ask', json={'question': 'how much did I spend this month?'}, headers=auth_headers)
    assert r.status_code == 200 and 'answer' in r.get_json()
    assert client.post('/api/ask', json={}, headers=auth_headers).status_code == 400
    assert client.post('/api/ask', json={'question': 'x'}).status_code == 401
