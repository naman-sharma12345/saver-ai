"""Ask your money: answer plain-English questions about a student's own spending.

No LLM and no outside calls. A small TF-IDF + logistic regression model picks the intent; dates,
categories and merchants are pulled out with rules. Answers are computed from the expense rows.
"""
import re
from collections import defaultdict
from datetime import date, datetime, timedelta

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

TRAIN = {
    'total': ['how much did i spend', 'total spending', 'what did i spend', 'how much have i spent', 'my total expenses',
              'how much money did i spend this month', 'spend on food', 'how much on transport', 'how much did i spend at swiggy',
              'what is my spending', 'sum of my expenses', 'how much was spent'],
    'biggest': ['biggest expense', 'largest purchase', 'what was my most expensive purchase', 'highest spend', 'costliest thing i bought',
                'what was the biggest thing i paid for', 'top expense', 'most i spent on one thing'],
    'top_category': ['where does my money go', 'which category do i spend the most on', 'top spending category', 'what do i spend most on',
                     'biggest category', 'what eats most of my money', 'category breakdown', 'spending by category'],
    'count': ['how many expenses', 'how many times did i order', 'number of transactions', 'how many purchases did i make',
              'count of payments', 'how many times did i spend'],
    'average': ['average spend per day', 'daily average', 'how much do i spend per day on average', 'average expense',
                'typical spending per day', 'mean daily spend'],
    'compare': ['am i spending more than last month', 'compare this month to last month', 'spending more than usual', 'is my spending going up',
                'am i spending less than before', 'how does this month compare', 'change in spending vs last month', 'am i overspending compared to before'],
    'recent': ['show my latest expenses', 'recent purchases', 'what did i buy lately', 'last transactions', 'list my recent spending',
               'what were my last payments'],
    'left': ['how much do i have left', 'how much money is left', 'remaining allowance', 'what is left of my allowance', 'can i afford',
             'how much can i still spend', 'balance left this month'],
}

CATEGORY_WORDS = {
    'Food': ['food', 'eat', 'eating', 'meal', 'meals', 'lunch', 'dinner', 'breakfast', 'snack', 'snacks', 'canteen', 'restaurant', 'swiggy', 'zomato', 'chai', 'coffee'],
    'Transport': ['transport', 'travel', 'commute', 'cab', 'uber', 'ola', 'bus', 'metro', 'auto', 'petrol', 'fuel', 'ride', 'rides'],
    'Study Materials': ['study', 'books', 'book', 'stationery', 'course', 'courses', 'notes', 'xerox', 'printing'],
    'Entertainment': ['entertainment', 'movie', 'movies', 'netflix', 'games', 'gaming', 'fun', 'party', 'concert'],
    'Shopping': ['shopping', 'clothes', 'clothing', 'amazon', 'flipkart', 'myntra', 'shoes'],
    'Bills': ['bills', 'bill', 'rent', 'recharge', 'electricity', 'wifi', 'internet'],
    'Health': ['health', 'medicine', 'medicines', 'doctor', 'pharmacy', 'gym'],
}

PRO_INTENTS = {'compare'}

_model = None


def _intent_model():
    global _model
    if _model is None:
        X, y = [], []
        for label, phrases in TRAIN.items():
            for p in phrases:
                X.append(p)
                y.append(label)
        _model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                               LogisticRegression(C=20, max_iter=500))
        _model.fit(X, y)
    return _model


def classify(question):
    m = _intent_model()
    probs = m.predict_proba([question.lower()])[0]
    i = probs.argmax()
    return str(m.classes_[i]), float(probs[i])


def parse_period(q, today=None):
    """Return (start_date, end_date_inclusive, label)."""
    today = today or date.today()
    q = q.lower()
    first = today.replace(day=1)
    if 'yesterday' in q:
        d = today - timedelta(days=1)
        return d, d, 'yesterday'
    if 'today' in q:
        return today, today, 'today'
    if 'last week' in q:
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6), 'last week'
    if 'this week' in q:
        return today - timedelta(days=today.weekday()), today, 'this week'
    if 'last month' in q:
        end = first - timedelta(days=1)
        return end.replace(day=1), end, 'last month'
    m = re.search(r'(?:last|past)\s+(\d{1,3})\s+days', q)
    if m:
        n = max(1, min(int(m.group(1)), 365))
        return today - timedelta(days=n - 1), today, 'the last %d days' % n
    if 'this year' in q:
        return today.replace(month=1, day=1), today, 'this year'
    return first, today, 'this month'


def find_category(q):
    words = set(re.findall(r'[a-z]+', q.lower()))
    for cat, ws in CATEGORY_WORDS.items():
        if cat.lower() in q.lower() or words & set(ws):
            return cat
    return None


def find_merchant(q, expenses):
    ql = q.lower()
    names = {(e.store_name or '').strip() for e in expenses}
    best = None
    for n in names:
        if len(n) >= 3 and n.lower() in ql and (best is None or len(n) > len(best)):
            best = n
    return best


def _day(e):
    c = e.created_at
    return c.date() if isinstance(c, datetime) else c


def _inr(x):
    return 'Rs {:,.0f}'.format(x)


def answer(question, expenses, allowance=0.0, today=None, is_pro=True):
    today = today or date.today()
    intent, conf = classify(question)
    start, end, label = parse_period(question, today)
    cat = find_category(question)
    merchant = find_merchant(question, expenses)

    def in_range(e, s=start, t=end):
        return s <= _day(e) <= t

    pool = [e for e in expenses if (not cat or e.category == cat) and (not merchant or (e.store_name or '').strip() == merchant)]
    rows = [e for e in pool if in_range(e)]
    scope = ' on %s' % cat if cat else (' at %s' % merchant if merchant else '')
    out = {'intent': intent, 'confidence': round(conf, 2), 'period': label, 'locked': False}

    if intent in PRO_INTENTS and not is_pro:
        out.update(locked=True, answer='Comparing periods is a Pro feature. Upgrade to see how this month stacks up against last.')
        return out

    if conf < 0.18:
        out.update(intent='unknown', answer='I did not catch that. Try "how much did I spend on food this month?" or "what was my biggest expense last week?"')
        return out

    if intent == 'total':
        total = sum(e.amount for e in rows)
        out.update(value=round(total, 2), answer='You spent %s%s %s across %d payment%s.' % (_inr(total), scope, label, len(rows), '' if len(rows) == 1 else 's'))
    elif intent == 'count':
        out.update(value=len(rows), answer='%d payment%s%s %s.' % (len(rows), '' if len(rows) == 1 else 's', scope, label))
    elif intent == 'biggest':
        if not rows:
            out['answer'] = 'No expenses%s %s.' % (scope, label)
        else:
            e = max(rows, key=lambda x: x.amount)
            out.update(value=round(e.amount, 2), answer='Your biggest%s %s was %s at %s on %s.' % (' ' + cat if cat else '', label, _inr(e.amount), e.store_name or e.description, _day(e).strftime('%d %b')))
    elif intent == 'top_category':
        by = defaultdict(float)
        for e in expenses:
            if in_range(e):
                by[e.category] += e.amount
        if not by:
            out['answer'] = 'No spending %s yet.' % label
        else:
            ranked = sorted(by.items(), key=lambda kv: -kv[1])
            total = sum(by.values())
            out.update(breakdown=[{'category': k, 'amount': round(v, 2)} for k, v in ranked[:5]],
                       answer='%s %s: %s (%d%% of %s).' % ('Most of your money went to', label, ranked[0][0], round(ranked[0][1] / total * 100), _inr(total)))
    elif intent == 'average':
        days = max(1, (min(end, today) - start).days + 1)
        total = sum(e.amount for e in rows)
        out.update(value=round(total / days, 2), answer='About %s a day%s %s.' % (_inr(total / days), scope, label))
    elif intent == 'recent':
        last = sorted(pool, key=lambda e: e.created_at, reverse=True)[:5]
        out.update(rows=[{'store': e.store_name, 'amount': e.amount, 'date': _day(e).isoformat()} for e in last],
                   answer='Your latest payments: ' + (', '.join('%s %s' % (e.store_name or e.description, _inr(e.amount)) for e in last) or 'none yet') + '.')
    elif intent == 'left':
        first = today.replace(day=1)
        spent = sum(e.amount for e in expenses if first <= _day(e) <= today)
        if allowance:
            out.update(value=round(allowance - spent, 2), answer='You have %s left of your %s allowance this month.' % (_inr(max(0, allowance - spent)), _inr(allowance)))
        else:
            out['answer'] = 'Set your monthly allowance in Profile and I can tell you what is left.'
    elif intent == 'compare':
        first = today.replace(day=1)
        prev_end = first - timedelta(days=1)
        day_n = today.day
        prev_same = prev_end.replace(day=min(day_n, prev_end.day))
        cur = sum(e.amount for e in pool if first <= _day(e) <= today)
        prev = sum(e.amount for e in pool if prev_end.replace(day=1) <= _day(e) <= prev_same)
        if prev == 0:
            out['answer'] = 'No spending%s in the same stretch of last month to compare with.' % scope
        else:
            pct = round((cur - prev) / prev * 100)
            out.update(value=pct, answer='Up to day %d you have spent %s%s, %s than the %s at this point last month (%d%% %s).' % (
                day_n, _inr(cur), scope, 'more' if pct > 0 else 'less', _inr(prev), abs(pct), 'higher' if pct > 0 else 'lower'))
    return out
