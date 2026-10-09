"""Logging streaks and milestone badges. Plain date arithmetic over the user's own expenses."""
from datetime import date, datetime, timedelta

MILESTONES = [(3, 'Getting going'), (7, 'One week'), (14, 'Two weeks'), (30, 'Habit locked in'), (60, 'Two months'), (100, 'Hundred days')]


def _day(v):
    return v.date() if isinstance(v, datetime) else v


def streak_summary(expenses, today=None):
    today = today or date.today()
    days = sorted({_day(e.created_at) for e in expenses if e.created_at and _day(e.created_at) <= today})
    best = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        best = max(best, run)
        prev = d
    have = set(days)
    cur = today if today in have else today - timedelta(days=1)
    current = 0
    while cur in have:
        current += 1
        cur -= timedelta(days=1)
    nxt = next(((n, name) for n, name in MILESTONES if n > current), None)
    return {
        'current': current, 'best': best, 'logged_today': today in have,
        'badges': [{'days': n, 'name': name, 'earned': best >= n} for n, name in MILESTONES],
        'next_milestone': {'days': nxt[0], 'name': nxt[1], 'to_go': nxt[0] - current} if nxt else None,
    }
