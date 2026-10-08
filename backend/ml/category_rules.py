"""Categories the user taught SaverAI. When someone fixes a category, every later expense from
the same merchant gets that category first, before the model is asked."""
import re

from app import db
from models import CategoryRule


def merchant_key(store_name, description=''):
    t = (store_name or description or '').lower()
    t = re.sub(r'\d+', ' ', t)
    t = re.sub(r'[^a-z ]+', ' ', t)
    return ' '.join(t.split())[:120]


def rule_category(user_id, store_name, description=''):
    key = merchant_key(store_name, description)
    if not key:
        return None
    rule = CategoryRule.query.filter_by(user_id=user_id, merchant_key=key).first()
    return rule.category if rule else None


def learn_rule(user_id, store_name, description, category):
    """Remember category for this merchant. Returns the rule dict, or None if there is no merchant."""
    key = merchant_key(store_name, description)
    category = (category or '').strip()[:50]
    if not key or not category:
        return None
    rule = CategoryRule.query.filter_by(user_id=user_id, merchant_key=key).first()
    if rule:
        rule.category = category
    else:
        rule = CategoryRule(user_id=user_id, merchant_key=key, category=category)
        db.session.add(rule)
    return rule.to_dict() if rule.id else {'merchant': key, 'category': category}
