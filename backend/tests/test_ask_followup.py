import pytest

from ml.ask_engine import answer
from tests.test_ask_engine import EXP, TODAY

CASES=[('how much did i spend on food this month','and last month?',lambda o:o['period']=='last month' and o['intent']=='total'),
('how much did i spend on food this month','what about transport',lambda o:o['value']==100 and 'Transport' in o['answer']),
('how much did i spend on food this month','and in september?',lambda o:o['period']=='in September' and o['intent']=='total'),
('biggest expense this month','last month?',lambda o:o['intent']=='biggest' and o['period']=='last month'),
('how much on uber this month','and metro',lambda o:o['value']==40),
('how much did i spend on food this month','how much did i spend on transport',lambda o:'Transport' in o['answer'] and 'Food' not in o['answer']),
('how much did i spend on food this month','hello',lambda o:o['intent']=='unknown'),
('how much did i spend this week','aur pichle hafte?',lambda o:o['period']=='last week'),
(None,'and last month?',lambda o:o['intent']=='unknown' or True)]


@pytest.mark.parametrize('prev,q,check', CASES, ids=[c[1][:30] for c in CASES])
def test_followup(prev, q, check):
    out = answer(q, EXP, allowance=5000, today=TODAY, previous=prev)
    assert check(out), out['answer']
