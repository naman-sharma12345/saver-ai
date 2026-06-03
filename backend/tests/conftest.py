"""
Shared test fixtures for the Student Expense Manager test suite.
"""

import sys
import os
import pytest

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db as _db
from models import User, Expense, Category, Budget, Store
import bcrypt


@pytest.fixture(scope='session')
def app():
    """Create a test application with an in-memory SQLite database."""
    app = create_app('testing')
    with app.app_context():
        _db.create_all()

        # Seed basic data
        pw_hash = bcrypt.hashpw(b'Test@123', bcrypt.gensalt()).decode('utf-8')

        student = User(
            email='student@test.com',
            password_hash=pw_hash,
            role='student',
            name='Test Student',
            monthly_allowance=15000.0,
        )
        parent = User(
            email='parent@test.com',
            password_hash=pw_hash,
            role='parent',
            name='Test Parent',
        )
        _db.session.add_all([student, parent])
        _db.session.commit()

        student.parent_id = parent.id
        _db.session.commit()

        # Seed categories
        for name in ['Food', 'Transport', 'Study Materials', 'Entertainment',
                      'Shopping', 'Bills', 'Health', 'Other']:
            _db.session.add(Category(name=name, is_custom=False))
        _db.session.commit()

        # Seed some expenses
        from datetime import datetime, timedelta, timezone
        import random
        random.seed(42)

        expense_data = [
            (250, 'Food', 'Lunch at canteen', 'Amul Canteen'),
            (450, 'Food', 'Dominos pizza', 'Dominos'),
            (200, 'Transport', 'Uber ride', 'Uber'),
            (150, 'Transport', 'Metro recharge', 'Noida Metro'),
            (550, 'Study Materials', 'DBMS textbook', 'Book Store'),
            (500, 'Entertainment', 'Movie ticket', 'PVR'),
            (1299, 'Shopping', 'Wireless earbuds', 'Amazon'),
            (399, 'Bills', 'Jio recharge', 'Jio'),
            (350, 'Health', 'Medicine', 'Apollo Pharmacy'),
            (120, 'Food', 'Coffee at CCD', 'CCD'),
            (80, 'Transport', 'Auto fare', 'Auto'),
            (899, 'Study Materials', 'Udemy course', 'Udemy'),
            (199, 'Entertainment', 'Spotify premium', 'Spotify'),
            (799, 'Shopping', 'T-shirt', 'Myntra'),
            (500, 'Bills', 'Electricity bill', 'Noida Power'),
            (5000, 'Shopping', 'Laptop bag premium', 'Amazon'),  # anomaly candidate
        ]

        now = datetime.now(timezone.utc)
        for i, (amt, cat, desc, store) in enumerate(expense_data):
            days_ago = random.randint(0, 60)
            exp = Expense(
                user_id=1,
                amount=amt,
                category=cat,
                description=desc,
                store_name=store,
                location_lat=28.627 + random.uniform(-0.005, 0.005),
                location_lng=77.365 + random.uniform(-0.005, 0.005),
                created_at=now - timedelta(days=days_ago),
                updated_at=now - timedelta(days=days_ago),
            )
            _db.session.add(exp)
        _db.session.commit()

        # Seed budgets
        current_month = now.replace(day=1).date()
        for cat, limit in [('Food', 3000), ('Transport', 1500), ('Study Materials', 2000),
                            ('Entertainment', 1500), ('Shopping', 2000), ('Bills', 1500),
                            ('Health', 1000), ('Other', 500)]:
            _db.session.add(Budget(user_id=1, category=cat, budget_limit=limit, month=current_month))
        _db.session.commit()

        # Seed stores
        stores = [
            {'name': 'Amul Canteen', 'category': 'Food', 'lat': 28.6275, 'lng': 77.3655, 'address': 'Sec 62', 'average_price_level': 1},
            {'name': 'Dominos', 'category': 'Food', 'lat': 28.626, 'lng': 77.364, 'address': 'Sec 62', 'average_price_level': 3},
            {'name': 'Kanha Stationery', 'category': 'Study Materials', 'lat': 28.6265, 'lng': 77.3652, 'address': 'Sec 62', 'average_price_level': 1},
            {'name': 'Apollo Pharmacy', 'category': 'Health', 'lat': 28.628, 'lng': 77.3642, 'address': 'Sec 62', 'average_price_level': 3},
            {'name': 'Reliance Digital', 'category': 'Shopping', 'lat': 28.6255, 'lng': 77.367, 'address': 'Sec 62', 'average_price_level': 4},
        ]
        for s in stores:
            _db.session.add(Store(**s))
        _db.session.commit()

        yield app

        _db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Get JWT auth headers for the test student."""
    resp = client.post('/api/auth/login', json={
        'email': 'student@test.com',
        'password': 'Test@123',
    })
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def parent_headers(client):
    """Get JWT auth headers for the test parent."""
    resp = client.post('/api/auth/login', json={
        'email': 'parent@test.com',
        'password': 'Test@123',
    })
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
