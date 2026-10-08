"""Weekly spending digest. Plain arithmetic over the user's own expenses, no outside services."""
from collections import defaultdict
from datetime import date, datetime, timedelta


def _day(value):
    return value.date() if isinstance(value, datetime) else value


def logging_streak(expenses, today):
    """Consecutive days with at least one logged expense, ending today (or yesterday, so the
    streak is not lost before the user has had a chance to log today's spending)."""
    days = {_day(e.created_at) for e in expenses if e.created_at}
    cur = today if today in days else today - timedelta(days=1)
    n = 0
    while cur in days:
        n += 1
        cur -= timedelta(days=1)
    return n


def build_digest(expenses, subscriptions, today=None):
    """Last 7 days (ending today) compared with the 7 days before.

    expenses: objects with .created_at .amount .category .store_name .description
    subscriptions: output of detect_subscriptions
    """
    today = today or date.today()
    start = today - timedelta(days=6)
    prev_start = start - timedelta(days=7)
    this_week, prev_total = [], 0.0
    for e in expenses:
        if not e.created_at:
            continue
        d = _day(e.created_at)
        if start <= d <= today:
            this_week.append(e)
        elif prev_start <= d < start:
            prev_total += e.amount

    total = sum(e.amount for e in this_week)
    daily = defaultdict(float)
    cats = defaultdict(float)
    for e in this_week:
        daily[_day(e.created_at)] += e.amount
        cats[e.category or 'Other'] += e.amount
    days = [{'date': (start + timedelta(days=i)).isoformat(),
             'amount': round(daily.get(start + timedelta(days=i), 0.0), 2)} for i in range(7)]

    top_cat = max(cats.items(), key=lambda kv: kv[1]) if cats else None
    biggest = max(this_week, key=lambda e: e.amount) if this_week else None
    change = None
    if prev_total > 0:
        change = round((total - prev_total) / prev_total * 100, 1)

    upcoming = []
    for s in subscriptions:
        try:
            nxt = _day(datetime.fromisoformat(s['next_expected']))
        except (KeyError, ValueError):
            continue
        if today <= nxt <= today + timedelta(days=7):
            upcoming.append({'merchant': s['merchant'], 'amount': s['amount'], 'date': nxt.isoformat()})
    upcoming.sort(key=lambda u: u['date'])

    if not this_week:
        headline = 'No spending recorded in the last 7 days.'
    elif change is None:
        headline = f'You spent Rs {total:,.0f} in the last 7 days.'
    elif change <= -5:
        headline = f'Nice week: spending is down {abs(change):.0f}% from the week before.'
    elif change >= 5:
        headline = f'Spending is up {change:.0f}% from the week before.'
    else:
        headline = 'Spending was about the same as the week before.'

    return {
        'headline': headline,
        'period': {'start': start.isoformat(), 'end': today.isoformat()},
        'total': round(total, 2),
        'previous_total': round(prev_total, 2),
        'change_percent': change,
        'daily': days,
        'no_spend_days': sum(1 for d in days if d['amount'] == 0),
        'top_category': {'name': top_cat[0], 'amount': round(top_cat[1], 2)} if top_cat else None,
        'biggest_expense': ({'description': (biggest.store_name or biggest.description or 'Expense'),
                             'amount': round(biggest.amount, 2), 'category': biggest.category}
                            if biggest else None),
        'upcoming_renewals': upcoming,
        'logging_streak': logging_streak(expenses, today),
    }
