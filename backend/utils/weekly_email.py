"""Opt-in Sunday summary email for parents. One email per parent, one block per linked student.

Same rules as the parent dashboard: only students whose account is active (consent granted), and only the
shape of the week (total, change, top category, no-spend days), never a purchase-by-purchase list.
"""
from models import Expense, User
from ml.digest import build_digest
from utils.mailer import send_email


def _block(student, d):
    name = (student.name or 'Your student').split()[0]
    lines = [name, '  ' + d['headline'].replace('You spent', 'Spent')]
    if d.get('top_category'):
        lines.append('  Mostly %s' % d['top_category']['name'])
    lines.append('  %d no-spend day%s' % (d['no_spend_days'], '' if d['no_spend_days'] == 1 else 's'))
    return '\n'.join(lines)


def compose(parent):
    """Return (subject, body) for this parent, or None if there is nothing to say."""
    kids = User.query.filter_by(parent_id=parent.id, role='student', consent_status='granted').all()
    if not kids:
        return None
    blocks = [_block(k, build_digest(Expense.query.filter_by(user_id=k.id).all(), [])) for k in kids]
    body = 'Your week on SaverAI\n\n' + '\n\n'.join(blocks) + (
        '\n\nThis is a summary, not a transaction feed. You can turn this email off any time on your SaverAI dashboard.')
    return 'Your weekly SaverAI summary', body


def send_weekly_parent_emails():
    sent = 0
    for parent in User.query.filter_by(role='parent', weekly_email=True).all():
        msg = compose(parent)
        if msg:
            send_email(parent.email, msg[0], msg[1])
            sent += 1
    return sent
