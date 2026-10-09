"""Ask your money: answer plain-English questions about a student's own spending.

No LLM and no outside calls. A small TF-IDF + logistic regression model picks the intent; dates,
categories and merchants are pulled out with rules. Answers are computed from the expense rows.
"""
import difflib
import re
from collections import defaultdict
from datetime import date, datetime, timedelta

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

TRAIN = {
    'total': ['how much did i spend', 'total spending', 'what did i spend', 'how much have i spent', 'my total expenses',
              'how much money did i spend this month', 'spend on food', 'how much on transport', 'how much did i spend at swiggy',
              'what is my spending', 'sum of my expenses', 'how much was spent', 'spend in last 7 days', 'spending last week', 'how much did i spend on 5 october', 'expenses on friday', 'how much in september', 'total on bills', 'what did i spend on food and transport'],
    'biggest': ['biggest expense', 'largest purchase', 'what was my most expensive purchase', 'highest spend', 'costliest thing i bought',
                'what was the biggest thing i paid for', 'top expense', 'most i spent on one thing', 'what is my biggest purchase on shopping', 'biggest food expense', 'most expensive thing this week', 'priciest thing i bought', 'costliest item last month'],
    'top_category': ['where does my money go', 'which category do i spend the most on', 'top spending category', 'what do i spend most on',
                     'biggest category', 'what eats most of my money', 'category breakdown', 'spending by category', 'which category is eating my budget', 'what category takes most of my budget', 'which category is using my allowance'],
    'count': ['how many expenses', 'how many times did i order', 'number of transactions', 'how many purchases did i make',
              'count of payments', 'how many times did i spend'],
    'average': ['average spend per day', 'daily average', 'how much do i spend per day on average', 'average expense',
                'typical spending per day', 'mean daily spend'],
    'compare': ['am i spending more than last month', 'compare this month to last month', 'spending more than usual', 'is my spending going up',
                'am i spending less than before', 'how does this month compare', 'change in spending vs last month', 'am i overspending compared to before', 'did i spend too much', 'am i overspending', 'is this month higher than last month', 'is my spending increasing', 'is my spending rising', 'did i spend more this month'],
    'recent': ['show my latest expenses', 'recent purchases', 'what did i buy lately', 'last transactions', 'list my recent spending',
               'what were my last payments', 'last 3 transactions', 'my 5 latest expenses', 'what did i buy on amazon', 'list purchases at swiggy', 'latest 4 expenses on food', 'last 2 purchases', 'show 10 recent payments'],
    'left': ['how much do i have left', 'how much money is left', 'remaining allowance', 'what is left of my allowance', 'can i afford',
             'how much can i still spend', 'balance left this month', 'am i broke', 'how much left in my budget', 'did i go over budget', 'am i over budget', 'how much of my budget is used', 'am i running out of money', 'will my money last this month', 'how much allowance remains'],
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


SLANG = {'wat': 'what', 'wht': 'what', 'hw': 'how', 'mch': 'much', 'mny': 'many', 'spnd': 'spend', 'spnt': 'spent', 'tims': 'times',
         'mnth': 'month', 'mnt': 'month', 'fod': 'food', 'ubr': 'uber', 'expnse': 'expense', 'expns': 'expense', 'xpense': 'expense',
         'wk': 'week', 'yday': 'yesterday', 'tdy': 'today', 'pls': '', 'plz': '', 'tht': 'that', 'abt': 'about', 'lst': 'last',
         'biggset': 'biggest', 'biggst': 'biggest', 'bgst': 'biggest', 'tranport': 'transport', 'transprt': 'transport',
         'cat': 'category', 'categ': 'category', 'txn': 'transaction', 'txns': 'transactions', 'amt': 'amount'}

# Hinglish (Roman Hindi) words mapped to the English the intent model knows.
HINGLISH_PHRASES = [
    (r'\bis\s+(?:mahine|mahina|month)\b', 'this month'), (r'\bis\s+(?:hafte|hafta|week)\b', 'this week'),
    (r'\bis\s+saal\b', 'this year'), (r'\b(?:pichle|pichhle|pehle)\s+(?:mahine|mahina)\b', 'last month'),
    (r'\b(?:pichle|pichhle)\s+(?:hafte|hafta)\b', 'last week'), (r'\bsabse\s+(?:bada|badaa|zyada|jyada)\b', 'biggest'),
    (r'\bkitne\s+(?:paise|rupaye|rupay)?\s*(?:bache|bacha|bachi|baki|baaki)\b', 'how much left'),
    (r'\b(?:paise|paisa|rupaye|rupay)\s+(?:kitne\s+)?(?:bache|bacha|bachi|baki|baaki)\b', 'how much left'),
    (r'\bkitn[aei]\s+(?:paise|paisa)?\s*(?:bacha|bache|bachi|baki)\b', 'how much left'),
    (r'\bkahan\s+(?:gaye|gaya|jata|jaata|jaate)\b', 'where does my money go'),
]
HINGLISH = {'kitna': 'how much', 'kitne': 'how much', 'kitni': 'how much', 'kharcha': 'spend', 'kharch': 'spend', 'kharche': 'spend',
            'kharcho': 'spend', 'kharchaa': 'spend', 'bada': 'biggest', 'bacha': 'left', 'bache': 'left', 'bachi': 'left',
            'mahine': 'month', 'mahina': 'month', 'hafte': 'week', 'hafta': 'week', 'aaj': 'today', 'kal': 'yesterday',
            'paise': 'money', 'paisa': 'money', 'rupaye': 'money', 'gaya': '', 'hua': '', 'kiya': '', 'kiye': '', 'tha': '',
            'hain': '', 'hai': '', 'pe': 'on', 'par': 'on', 'ka': '', 'ki': '', 'ke': '', 'mein': '', 'me': '', 'kya': '', 'ko': '',
            'se': '', 'mera': 'my', 'meri': 'my', 'mere': 'my', 'sabse': 'most', 'zyada': 'most', 'jyada': 'most', 'dikhao': 'show',
            'batao': '', 'bataiye': '', 'kab': 'when', 'kitni': 'how much', 'khana': 'food', 'khane': 'food', 'gaye': ''}

# Words that are already right: never "corrected" into something else.
COMMON = set("""a an the i my me we you it is are was were be been am do did does done have has had will would can could should shall may
might must of on in at to for from by with without about over under between and or but if then than so as not no yes how what which who
when where why much many more most less least all any some each every other another this that these those there here now just only also
too very really bro hey hi hello hii pls please tell show give list top best worst lowest highest per day days week weeks month months year
years ago last past next today yesterday tomorrow latest recent recently lately total sum count number average avg mean daily weekly monthly
spend spent spending expense expenses cost costs paid pay payment payments buy bought purchase purchases buy order ordered money rs inr
rupees allowance left remaining balance afford category categories compare compared usual before after times time out up down going
transaction transactions thing things stuff blow blew""".split())

MONTHS = {'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
          'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9, 'oct': 10, 'october': 10,
          'nov': 11, 'november': 11, 'dec': 12, 'december': 12}

COMPARE_CUES = ('more', 'less', 'than', 'compare', 'compared', ' vs ', 'versus', 'going up', 'going down', 'overspend', 'too much', 'usual',
                'higher', 'lower', 'increase', 'increasing', 'decrease', 'decreasing', 'rising', 'growing', 'falling', 'change', 'trend', 'before')

_vocab_cache = None


def _vocab():
    global _vocab_cache
    if _vocab_cache is None:
        words = set(COMMON)
        for ps in TRAIN.values():
            for ph in ps:
                words.update(re.findall(r'[a-z]+', ph))
        for ws in CATEGORY_WORDS.values():
            words.update(ws)
        words.update(MONTHS)
        _vocab_cache = sorted(w for w in words if len(w) >= 3)
    return _vocab_cache


def normalize(question, merchants=()):
    """Lowercase, translate Roman-Hindi, fix slang and typos. Returns clean English-ish text."""
    q = ' ' + re.sub(r'[^a-z0-9\s]', ' ', question.lower()) + ' '
    for pat, rep in HINGLISH_PHRASES:
        q = re.sub(pat, ' ' + rep + ' ', q)
    known = set(_vocab()) | {m.lower() for m in merchants if m}
    vocab = sorted(known)
    out = []
    for t in q.split():
        if t in HINGLISH:
            out.append(HINGLISH[t])
            continue
        if t in SLANG:
            out.append(SLANG[t])
            continue
        if t in known or t.isdigit() or len(t) < 4:
            out.append(t)
            continue
        if re.match(r'^\d+(st|nd|rd|th)$', t):
            out.append(t)
            continue
        m = difflib.get_close_matches(t, vocab, n=1, cutoff=0.8)
        out.append(m[0] if m else t)
    return re.sub(r'\s+', ' ', ' '.join(out)).strip()


DOMAIN_WORDS = {'spend', 'spent', 'spending', 'expense', 'expenses', 'cost', 'paid', 'pay', 'payment', 'payments', 'buy', 'bought',
                'purchase', 'purchases', 'money', 'allowance', 'left', 'remaining', 'balance', 'category', 'categories', 'transaction',
                'transactions', 'order', 'ordered', 'afford', 'blow', 'blew', 'rs', 'inr', 'rupees', 'biggest', 'largest', 'costliest', 'budget', 'expensive', 'costly', 'priciest', 'broke', 'average', 'avg', 'mean', 'daily', 'total', 'sum', 'count'}


def in_domain(q, merchants):
    words = set(re.findall(r'[a-z]+', q))
    if words & DOMAIN_WORDS:
        return True
    if any(words & set(ws) for ws in CATEGORY_WORDS.values()):
        return True
    if any(m and m.lower() in q for m in merchants):
        return True
    return False


def parse_dates(q, today):
    """Explicit dates: '5th october', 'on 5 oct', 'between 1 oct and 7 oct', 'in september'. Returns (start, end, label) or None."""
    def mk(day, mon):
        yr = today.year
        try:
            d = date(yr, mon, day)
        except ValueError:
            return None
        return d if d <= today else date(yr - 1, mon, day)
    pat = r'(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s+)?(' + '|'.join(sorted(MONTHS, key=len, reverse=True)) + r')\b'
    hits = [(int(a), MONTHS[b]) for a, b in re.findall(pat, q)]
    if not hits:
        pat2 = r'(' + '|'.join(sorted(MONTHS, key=len, reverse=True)) + r')\s+(\d{1,2})(?:st|nd|rd|th)?\b'
        hits = [(int(b), MONTHS[a]) for a, b in re.findall(pat2, q)]
    ds = [mk(d, m) for d, m in hits[:2]]
    ds = [d for d in ds if d]
    if len(ds) == 2:
        a, b = sorted(ds)
        return a, b, 'from %s to %s' % (a.strftime('%d %b'), b.strftime('%d %b'))
    if len(ds) == 1:
        return ds[0], ds[0], 'on ' + ds[0].strftime('%d %b')
    m = re.search(r'\b(?:in|during|for|of)\s+(' + '|'.join(sorted(MONTHS, key=len, reverse=True)) + r')\b', q)
    if m:
        mon = MONTHS[m.group(1)]
        yr = today.year if mon <= today.month else today.year - 1
        start = date(yr, mon, 1)
        end = (date(yr + (mon == 12), mon % 12 + 1, 1) - timedelta(days=1))
        return start, min(end, today), 'in ' + start.strftime('%B')
    return None


def parse_limit(q, default=5):
    m = re.search(r'\b(?:last|latest|recent|top|first)\s+(\d{1,2})\b(?!\s*days?)', q) or re.search(r'\b(\d{1,2})\s+(?:latest|recent|last)\b', q)
    return max(1, min(int(m.group(1)), 20)) if m else default


def parse_period(q, today=None):
    """Return (start_date, end_date_inclusive, label)."""
    today = today or date.today()
    q = q.lower()
    first = today.replace(day=1)
    explicit = parse_dates(q, today)
    if explicit:
        return explicit
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
        return today - timedelta(days=n - 1), today, 'in the last %d days' % n
    if 'this year' in q:
        return today.replace(month=1, day=1), today, 'this year'
    return first, today, 'this month'


def find_categories(q, merchant_names=()):
    """All categories mentioned. A word that is also a merchant in the user's data counts as the merchant, not the category."""
    words = set(re.findall(r'[a-z]+', q.lower())) - {m.lower() for m in merchant_names}
    return [cat for cat, ws in CATEGORY_WORDS.items() if cat.lower() in q.lower() or words & set(ws)]


def find_category(q):
    c = find_categories(q)
    return c[0] if c else None


def find_merchants(q, expenses):
    ql = q.lower()
    names = {(e.store_name or '').strip() for e in expenses}
    found = [n for n in names if len(n) >= 3 and re.search(r'\b' + re.escape(n.lower()) + r'\b', ql)]
    return sorted(found, key=len, reverse=True)


def find_merchant(q, expenses):
    f = find_merchants(q, expenses)
    return f[0] if f else None


def _day(e):
    c = e.created_at
    return c.date() if isinstance(c, datetime) else c


def _inr(x):
    return 'Rs {:,.0f}'.format(x)


_PERIOD_RE = re.compile(
    r'\b(?:this|last|past)\s+(?:month|week|year)\b|\b(?:today|yesterday)\b|\b(?:in\s+)?(?:the\s+)?(?:last|past)\s+\d{1,3}\s+days\b'
    r'|\b(?:on|from)\s+\d{1,2}(?:st|nd|rd|th)?\s+[a-z]+(?:\s+(?:to|and)\s+\d{1,2}(?:st|nd|rd|th)?\s+[a-z]+)?\b|\b(?:in|during)\s+(?:' + '|'.join(MONTHS) + r')\b')
_OPENER_RE = re.compile(r'^(?:and|also|ok(?:ay)?|what about|how about|aur|or|same for|and what about)\s+')
_QUESTION_WORDS = {'how', 'what', 'which', 'show', 'list', 'tell', 'did', 'do', 'am', 'is', 'can', 'where', 'who', 'when'}


def is_followup(q, previous, merchants=()):
    """A short fragment that only makes sense after the previous question: "and last month?", "what about transport"."""
    if not previous:
        return False
    if _OPENER_RE.match(q):
        return True
    words = q.split()
    if len(words) > 3 or (set(words) & (DOMAIN_WORDS | _QUESTION_WORDS)):
        return False
    return bool(_PERIOD_RE.search(q) or parse_dates(q, date.today()) or find_categories(q, merchants) or any(m.lower() in q for m in merchants))


def merge_followup(prev, q, merchants):
    """Rebuild a full question from the previous one plus the new fragment (new period / category / merchant replaces the old)."""
    frag = _OPENER_RE.sub('', q).strip()
    base = prev
    if _PERIOD_RE.search(frag) or parse_dates(frag, date.today()):
        base = _PERIOD_RE.sub(' ', base)
    new_words = set(re.findall(r'[a-z]+', frag))
    if find_categories(frag, merchants) or any(m.lower() in frag for m in merchants):
        drop = {w for ws in CATEGORY_WORDS.values() for w in ws} | {m.lower() for m in merchants} | {c.lower() for c in CATEGORY_WORDS}
        base = ' '.join(w for w in base.split() if w not in drop or w in new_words)
    return re.sub(r'\s+', ' ', base + ' ' + frag).strip()


def answer(question, expenses, allowance=0.0, today=None, is_pro=True, previous=None):
    today = today or date.today()
    names = sorted({(e.store_name or '').strip() for e in expenses if (e.store_name or '').strip()})
    q = normalize(question, names)
    followup = False
    if previous and is_followup(q, normalize(previous, names), names):
        q = merge_followup(normalize(previous, names), q, names)
        followup = True
    start, end, label = parse_period(q, today)
    explicit_period = label not in ('this month',) or bool(re.search(r'\bthis month\b', q))
    intent, conf = classify(q)
    cue = any(c in ' %s ' % q for c in COMPARE_CUES)
    if intent == 'compare' and not cue:
        intent = 'total'  # "spend in last 7 days" is a total, not a comparison
    if cue and re.search(r'\b(too much|overspend\w*)\b', q) and intent in ('total', 'left'):
        intent = 'compare'
    if re.search(r'\b(delete|remove|add|edit|change|update|create|export|reset|clear|set)\b', q) and not re.search(r'\b(how much|how many|what|which|show|list)\b', q):
        return {'intent': 'unsupported', 'confidence': 1.0, 'period': label, 'locked': False,
                'answer': 'I can only answer questions about your spending. To add, edit or delete expenses, use the Expenses page.'}
    if re.search(r'\b(save|saving|savings|budget tips|advice|suggest|tips)\b', q) and not re.search(r'\b(how much|how many)\b', q):
        return {'intent': 'advice', 'confidence': 1.0, 'period': label, 'locked': False,
                'answer': 'For ideas on spending less, open Smart tips. To save toward something, set a goal on the Goals page.'}
    if re.search(r'\b(latest|recent|last|past)\s+\d{1,2}\s+(?:transactions?|purchases?|expenses?|payments?|things)\b', q) or re.search(r'\b\d{1,2}\s+(?:latest|recent)\b', q):
        intent = 'recent'
    merchants = find_merchants(q, expenses)
    cats = find_categories(q, merchants)
    cat = cats[0] if cats else None
    merchant = merchants[0] if merchants else None
    limit = parse_limit(q)
    in_cat = lambda e: (not cats or e.category in cats)
    in_mer = lambda e: (not merchants or (e.store_name or '').strip() in merchants)

    def in_range(e, s=start, t=end):
        return s <= _day(e) <= t

    pool = [e for e in expenses if in_cat(e) and in_mer(e)]
    rows = [e for e in pool if in_range(e)]
    if merchants:
        scope = ' at %s' % ' and '.join(merchants)
    elif cats:
        scope = ' on %s' % ' and '.join(cats)
    else:
        scope = ''
    cat = ' and '.join(cats) if cats and not merchants else None
    out = {'intent': intent, 'confidence': round(conf, 2), 'period': label, 'locked': False, 'followup': followup}

    if not in_domain(q, names) and not (explicit_period and re.search(r'\bhow much\b', q)):
        out.update(intent='unknown', confidence=0.0, answer='I only know about your own spending. Try "how much did I spend on food this month?" or "what was my biggest expense last week?"')
        return out

    if intent in PRO_INTENTS and not is_pro:
        out.update(locked=True, answer='Comparing periods is a Pro feature. Upgrade to see how this month stacks up against last.')
        return out

    if conf < 0.12:
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
                       answer='%s %s: %s (%d%% of %s).' % ('Top category', label, ranked[0][0], round(ranked[0][1] / total * 100), _inr(total)))
    elif intent == 'average':
        days = max(1, (min(end, today) - start).days + 1)
        total = sum(e.amount for e in rows)
        out.update(value=round(total / days, 2), answer='About %s a day%s %s.' % (_inr(total / days), scope, label))
    elif intent == 'recent':
        last = sorted(pool, key=lambda e: e.created_at, reverse=True)[:limit]
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
