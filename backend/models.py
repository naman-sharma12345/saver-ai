"""
SQLAlchemy models for the Student Expense Manager.
"""

from datetime import datetime, timezone
from app import db


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────
from plans import get_entitlement  # noqa: E402


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' | 'parent'
    name = db.Column(db.String(100), nullable=False)
    monthly_allowance = db.Column(db.Float, default=0.0)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Billing / entitlements (see plans.py). Times are naive UTC.
    plan = db.Column(db.String(20), nullable=False, default='free', server_default='free')  # 'free' | 'pro'
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    plan_expires_at = db.Column(db.DateTime, nullable=True)
    billing_ref = db.Column(db.String(100), nullable=True)  # provider subscription id
    email_verified = db.Column(db.Boolean, nullable=False, default=False, server_default='0')

    # DPDP: age, guardian consent for under-18s, and when the terms were accepted.
    date_of_birth = db.Column(db.Date, nullable=True)
    guardian_email = db.Column(db.String(120), nullable=True)
    consent_status = db.Column(db.String(20), nullable=False, default='granted', server_default='granted')  # granted | pending
    consent_at = db.Column(db.DateTime, nullable=True)
    terms_accepted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    parent = db.relationship('User', remote_side=[id], backref='children')
    expenses = db.relationship('Expense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('SavingRecommendation', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'name': self.name,
            'monthly_allowance': self.monthly_allowance,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'email_verified': bool(self.email_verified),
            'entitlement': get_entitlement(self),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Expense
# ─────────────────────────────────────────────────────────────────────────────
class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    description = db.Column(db.String(255), nullable=True)
    store_name = db.Column(db.String(120), nullable=True)
    location_lat = db.Column(db.Float, nullable=True)
    location_lng = db.Column(db.Float, nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    is_anomaly = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'store_name': self.store_name,
            'location_lat': self.location_lat,
            'location_lng': self.location_lng,
            'is_recurring': self.is_recurring,
            'is_anomaly': self.is_anomaly,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_custom = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_custom': self.is_custom,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Budget
# ─────────────────────────────────────────────────────────────────────────────
class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    budget_limit = db.Column(db.Float, nullable=False)
    month = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'budget_limit': self.budget_limit,
            'month': self.month.isoformat() if self.month else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Saving Recommendation
# ─────────────────────────────────────────────────────────────────────────────
class SavingRecommendation(db.Model):
    __tablename__ = 'saving_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recommendation_text = db.Column(db.Text, nullable=False)
    amount_saved = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recommendation_text': self.recommendation_text,
            'amount_saved': self.amount_saved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Store
# ─────────────────────────────────────────────────────────────────────────────
class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    average_price_level = db.Column(db.Integer, default=3)  # 1 (cheapest) – 5 (most expensive)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'lat': self.lat,
            'lng': self.lng,
            'address': self.address,
            'average_price_level': self.average_price_level,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Savings goal
# ─────────────────────────────────────────────────────────────────────────────
class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    saved_amount = db.Column(db.Float, nullable=False, default=0.0)
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CategoryRule(db.Model):
    """A category the user taught SaverAI for a merchant. Beats the model for that user."""
    __tablename__ = 'category_rules'
    __table_args__ = (db.UniqueConstraint('user_id', 'merchant_key', name='uq_rule_user_merchant'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    merchant_key = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {'id': self.id, 'merchant': self.merchant_key, 'category': self.category}


class AllowanceRequest(db.Model):
    """A student's request to a linked parent for extra money, and the parent's answer."""
    __tablename__ = 'allowance_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(140), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')  # pending | approved | declined
    parent_note = db.Column(db.String(140), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    decided_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self, student_name=None):
        return {
            'id': self.id, 'amount': self.amount, 'reason': self.reason, 'status': self.status,
            'parent_note': self.parent_note, 'student_name': student_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
        }
