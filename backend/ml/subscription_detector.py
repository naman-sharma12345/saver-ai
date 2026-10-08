"""
Recurring-charge (subscription) detection, implemented with our own local ML.

Pipeline:
  1. Normalise merchant names (store_name, else description) so "Spotify", "SPOTIFY 199" match.
  2. For each merchant with >= 2 charges compute features: charge count, coefficient of
     variation of the gaps between charges, coefficient of variation of the amounts, and
     how close the median gap is to a weekly / monthly / yearly cycle.
  3. A logistic-regression classifier (scikit-learn) scores "is this a subscription?".
     It is trained once, in-process, on synthetic recurring and non-recurring patterns
     generated with a fixed seed. No external model, API or key is involved.
"""
import re
import threading
from collections import defaultdict
from datetime import timedelta

import numpy as np
from sklearn.linear_model import LogisticRegression

CYCLES = {'weekly': 7, 'monthly': 30.4, 'yearly': 365}
_model = None
_lock = threading.Lock()


def normalize_merchant(text):
    t = (text or '').lower()
    t = re.sub(r'\d+', ' ', t)
    t = re.sub(r'[^a-z ]+', ' ', t)
    t = re.sub(r'\b(premium|plan|subscription|payment|bill|recharge|monthly|upi|pay)\b', ' ', t)
    return ' '.join(t.split())


def _cycle_closeness(median_gap):
    best = min(CYCLES.items(), key=lambda kv: abs(median_gap - kv[1]) / kv[1])
    return best[0], 1 - min(1.0, abs(median_gap - best[1]) / best[1])


def features(dates, amounts):
    """dates: sorted list of datetimes; amounts: same length."""
    gaps = np.diff([d.timestamp() / 86400 for d in dates])
    med = float(np.median(gaps))
    gap_cv = float(np.std(gaps) / med) if med > 0 else 5.0
    amt = np.asarray(amounts, dtype=float)
    amt_cv = float(np.std(amt) / amt.mean()) if amt.mean() > 0 else 5.0
    _, close = _cycle_closeness(med)
    return [min(len(dates), 12) / 12.0, min(gap_cv, 3.0), min(amt_cv, 3.0), close], med


def _synthetic(rng, n=1500):
    X, y = [], []
    for _ in range(n):
        cyc = rng.choice([7, 30.4, 365])
        k = int(rng.integers(2, 9))
        if rng.random() < 0.5:  # recurring
            gaps = cyc * (1 + rng.normal(0, 0.05, k - 1))
            amt_cv = abs(rng.normal(0.02, 0.03))
            label = 1
        else:  # ordinary spending at the same shop
            gaps = rng.exponential(cyc * rng.uniform(0.3, 2.0), k - 1) + 0.2
            amt_cv = rng.uniform(0.15, 1.2)
            label = 0
        med = float(np.median(gaps))
        gap_cv = float(np.std(gaps) / med)
        _, close = _cycle_closeness(med)
        X.append([min(k, 12) / 12.0, min(gap_cv, 3.0), min(amt_cv, 3.0), close])
        y.append(label)
    return np.array(X), np.array(y)


def get_model():
    global _model
    with _lock:
        if _model is None:
            X, y = _synthetic(np.random.default_rng(7))
            _model = LogisticRegression(max_iter=500).fit(X, y)
        return _model


def detect_subscriptions(expenses, min_confidence=0.7):
    """expenses: iterable of objects with .created_at .amount .store_name .description."""
    groups = defaultdict(list)
    for e in expenses:
        name = normalize_merchant(e.store_name or e.description)
        if name and e.created_at:
            groups[name].append(e)
    model = get_model()
    found = []
    for name, items in groups.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda e: e.created_at)
        dates = [i.created_at for i in items]
        amounts = [i.amount for i in items]
        feats, med = features(dates, amounts)
        conf = float(model.predict_proba([feats])[0][1])
        if conf < min_confidence:
            continue
        period, _ = _cycle_closeness(med)
        amount = float(np.median(amounts))
        per_month = amount * {'weekly': 4.35, 'monthly': 1, 'yearly': 1 / 12}[period]
        found.append({
            'merchant': (items[-1].store_name or items[-1].description or name).strip(),
            'amount': round(amount, 2),
            'period': period,
            'confidence': round(conf, 2),
            'charges': len(items),
            'last_charged': dates[-1].isoformat(),
            'next_expected': (dates[-1] + timedelta(days=CYCLES[period])).isoformat(),
            'monthly_cost': round(per_month, 2),
            'annual_cost': round(per_month * 12, 2),
        })
    found.sort(key=lambda s: -s['monthly_cost'])
    return found
