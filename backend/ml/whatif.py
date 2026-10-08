"""What-if savings simulator. Plain arithmetic over the last 30 days of spending."""
import math

MAX_CUT = 100


def simulate(spend_by_category, cuts, goals=()):
    """spend_by_category: {category: amount spent in the last 30 days}.
    cuts: {category: percent to cut, 0-100}. goals: dicts with name, target_amount, saved_amount.

    Returns each category's baseline and monthly saving, the totals, and how long the savings from
    these cuts alone would take to fill the nearest unfinished goal.
    """
    rows, monthly = [], 0.0
    for cat, spent in sorted(spend_by_category.items(), key=lambda kv: -kv[1]):
        try:
            pct = float(cuts.get(cat, 0))
        except (TypeError, ValueError):
            pct = 0.0
        pct = min(max(pct, 0.0), MAX_CUT)
        saving = spent * pct / 100.0
        monthly += saving
        rows.append({'category': cat, 'monthly_spend': round(spent, 2), 'cut_percent': pct,
                     'monthly_saving': round(saving, 2)})
    out = {'categories': rows, 'monthly_saving': round(monthly, 2), 'yearly_saving': round(monthly * 12, 2),
           'goal': None}
    open_goals = [g for g in goals if g['saved_amount'] < g['target_amount']]
    if open_goals:
        g = open_goals[0]
        remaining = g['target_amount'] - g['saved_amount']
        out['goal'] = {
            'name': g['name'], 'remaining': round(remaining, 2),
            'months': math.ceil(remaining / monthly) if monthly > 0 else None,
        }
    return out
