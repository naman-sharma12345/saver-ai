"""Month-end projection for each budget. Plain arithmetic, no outside services.

Projection = spent so far + (average daily spend so far) x days left. Very early in the month
the average is noisy, so for the first 3 days we only flag a category that is already over.
"""
import calendar
from datetime import date


def budget_pace(budgets, spent_by_category, today=None):
    """budgets: [{'category', 'budget_limit'}]; spent_by_category: {category: amount this month}."""
    today = today or date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    elapsed = today.day
    left = days_in_month - elapsed
    out = []
    for b in budgets:
        limit = float(b['budget_limit'])
        spent = float(spent_by_category.get(b['category'], 0.0))
        projected = spent + (spent / elapsed) * left
        if spent > limit:
            status = 'over'
        elif elapsed < 4:
            status = 'ok'
        elif projected > limit * 1.05:
            status = 'overshoot'
        elif projected > limit * 0.9:
            status = 'tight'
        else:
            status = 'ok'
        item = {'category': b['category'], 'limit': round(limit, 2), 'spent': round(spent, 2),
                'projected': round(projected, 2), 'status': status}
        if status == 'overshoot' and spent > 0:
            # Daily spend that would still land on the limit.
            item['safe_daily'] = round(max(limit - spent, 0) / left, 2) if left else 0.0
        out.append(item)
    order = {'over': 0, 'overshoot': 1, 'tight': 2, 'ok': 3}
    out.sort(key=lambda i: order[i['status']])
    return {'day': elapsed, 'days_in_month': days_in_month, 'items': out}
