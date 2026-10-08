"""Savings goal projections. Plain arithmetic on the student's own pace, no external services."""
from datetime import date, datetime, timedelta


def project_goal(goal, today=None, monthly_surplus=None):
    """Return progress, pace, projected finish date and what to save per month to hit the deadline.

    Pace comes from what the student has actually saved so far. If they have not saved anything yet,
    we fall back to their recent monthly surplus (allowance minus spending) when we know it.
    """
    today = today or date.today()
    target = float(goal.target_amount)
    saved = float(goal.saved_amount or 0)
    remaining = max(0.0, target - saved)
    created = goal.created_at.date() if isinstance(goal.created_at, datetime) else (goal.created_at or today)
    days = max(14, (today - created).days)  # a fresh goal has no real pace yet

    pace_month = (saved / days) * 30 if saved > 0 else None
    pace_source = 'saved' if pace_month else None
    if not pace_month and monthly_surplus and monthly_surplus > 0:
        pace_month, pace_source = float(monthly_surplus), 'surplus'

    done = remaining <= 0
    projected = None
    if done:
        projected = today
    elif pace_month and pace_month > 0:
        projected = today + timedelta(days=int(round(remaining / pace_month * 30)))

    needed_month = None
    status = 'done' if done else ('no_pace' if projected is None else 'on_track')
    if goal.deadline and not done:
        months_left = max((goal.deadline - today).days, 0) / 30
        needed_month = round(remaining / months_left, 2) if months_left > 0 else round(remaining, 2)
        if projected is not None:
            status = 'on_track' if projected <= goal.deadline else 'behind'
        elif goal.deadline < today:
            status = 'behind'

    return {
        'progress': round(min(1.0, saved / target), 4) if target > 0 else 0.0,
        'remaining': round(remaining, 2),
        'pace_per_month': round(pace_month, 2) if pace_month else None,
        'pace_source': pace_source,
        'projected_finish': projected.isoformat() if projected else None,
        'needed_per_month': needed_month,
        'status': status,
    }
