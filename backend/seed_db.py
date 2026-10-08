"""
Database seed script for SaverAI.

Creates realistic test users, diverse expenses with anomalies,
categories, and stores. Also trains the ML models automatically.
Usage:
    python seed_db.py
"""

import sys
import os
import io
import random
from datetime import datetime, timedelta, timezone
import bcrypt

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from plans import start_trial_end
from models import User, Expense, Category, Budget, SavingRecommendation, Store

def seed():
    app = create_app('development')

    with app.app_context():
        print("🌱 Seeding database...")

        # Create all tables
        db.create_all()

        # ─── Seed Categories ────────────────────────────────────────────
        default_categories = [
            'Food', 'Transport', 'Study Materials', 'Entertainment',
            'Shopping', 'Bills', 'Health', 'Other',
        ]

        for name in default_categories:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, is_custom=False))
        db.session.commit()
        print(f"  ✅ {len(default_categories)} default categories seeded.")

        # ─── Seed Users ─────────────────────────────────────────────────
        password = 'Test@123'
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Parent
        parent_email = 'parent@test.com'
        parent = User.query.filter_by(email=parent_email).first()
        if not parent:
            parent = User(email=parent_email, password_hash=pw_hash, role='parent', name='Mr. Sharma', monthly_allowance=0.0)
            db.session.add(parent)
            db.session.commit()

        # Student 1 (Good habits, linked to parent)
        student1_email = 'student1@test.com'
        student1 = User.query.filter_by(email=student1_email).first()
        if not student1:
            student1 = User(email=student1_email, password_hash=pw_hash, role='student', name='Rahul Sharma', monthly_allowance=15000.0, parent_id=parent.id, trial_ends_at=start_trial_end())
            db.session.add(student1)
            db.session.commit()

        # Student 2 (Bad habits, overspending)
        student2_email = 'student2@test.com'
        student2 = User.query.filter_by(email=student2_email).first()
        if not student2:
            student2 = User(email=student2_email, password_hash=pw_hash, role='student', name='Ayesha Khan', monthly_allowance=12000.0, trial_ends_at=start_trial_end())
            db.session.add(student2)
            db.session.commit()

        print(f"  ✅ Users created (Parent + 2 Students)")

        # ─── Seed Expenses ──────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        
        # Helper to generate expenses
        def generate_expenses_for_user(user_id, is_good_habit):
            if Expense.query.filter_by(user_id=user_id).count() > 0:
                return

            base_expenses = [
                {'amount': 250, 'category': 'Food', 'description': 'Lunch at Amul canteen', 'store_name': 'Amul Canteen Sec-62'},
                {'amount': 150, 'category': 'Transport', 'description': 'Metro card recharge', 'store_name': 'Noida Metro'},
                {'amount': 550, 'category': 'Study Materials', 'description': 'DBMS textbook', 'store_name': 'Technical Books Store'},
            ]

            if not is_good_habit:
                # Add expensive/anomalous items for bad habit student
                base_expenses.extend([
                    {'amount': 4500, 'category': 'Entertainment', 'description': 'VIP Concert Tickets', 'store_name': 'BookMyShow'},
                    {'amount': 3000, 'category': 'Shopping', 'description': 'Designer Jacket', 'store_name': 'Zara'},
                    {'amount': 800, 'category': 'Food', 'description': 'Fine dining', 'store_name': 'Barbeque Nation'},
                ])
            else:
                # Normal spending for good habit student
                base_expenses.extend([
                    {'amount': 450, 'category': 'Food', 'description': 'Dominos pizza with friends', 'store_name': 'Dominos Sec-62'},
                    {'amount': 649, 'category': 'Entertainment', 'description': 'Netflix subscription', 'store_name': 'Netflix'},
                ])

            for _ in range(3): # Duplicate base expenses over 3 months
                for exp in base_expenses:
                    # Randomize amounts slightly for variation
                    amt = exp['amount'] * random.uniform(0.9, 1.1)
                    days_ago = random.randint(0, 90)
                    created = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    
                    expense = Expense(
                        user_id=user_id,
                        amount=amt,
                        category=exp['category'],
                        description=exp['description'],
                        store_name=exp['store_name'],
                        location_lat=28.6270 + random.uniform(-0.005, 0.005),
                        location_lng=77.3650 + random.uniform(-0.005, 0.005),
                        created_at=created,
                        updated_at=created,
                    )
                    db.session.add(expense)
            db.session.commit()

        generate_expenses_for_user(student1.id, is_good_habit=True)
        generate_expenses_for_user(student2.id, is_good_habit=False)
        print(f"  ✅ Expenses seeded with distinct spending profiles.")

        # ─── Seed Budgets ───────────────────────────────────────────────
        current_month = now.replace(day=1).date()
        for student_id in [student1.id, student2.id]:
            if Budget.query.filter_by(user_id=student_id, month=current_month).count() == 0:
                budget_data = [
                    ('Food', 3000), ('Transport', 1500), ('Study Materials', 2000),
                    ('Entertainment', 1500), ('Shopping', 2000), ('Bills', 1500),
                    ('Health', 1000), ('Other', 500),
                ]
                for cat, limit in budget_data:
                    db.session.add(Budget(user_id=student_id, category=cat, budget_limit=limit, month=current_month))
        db.session.commit()

        # ─── Seed Stores ────────────────────────────────────────────────
        if Store.query.count() == 0:
            stores_data = [
                {'name': 'Amul Canteen', 'category': 'Food', 'lat': 28.6275, 'lng': 77.3655, 'address': 'A Block, Sector 62, Noida', 'average_price_level': 1},
                {'name': 'Dominos Pizza', 'category': 'Food', 'lat': 28.6260, 'lng': 77.3640, 'address': 'C Block, Sector 62, Noida', 'average_price_level': 3},
                {'name': 'Cafe Coffee Day', 'category': 'Food', 'lat': 28.6282, 'lng': 77.3662, 'address': 'Main Road, Sector 62, Noida', 'average_price_level': 3},
                {'name': 'Biryani Blues', 'category': 'Food', 'lat': 28.6250, 'lng': 77.3630, 'address': 'Near NSEZ Gate, Sector 62, Noida', 'average_price_level': 2},
                {'name': 'Technical Books Store', 'category': 'Study Materials', 'lat': 28.6273, 'lng': 77.3645, 'address': 'B Block, Sector 62, Noida', 'average_price_level': 2},
            ]
            for s in stores_data:
                db.session.add(Store(**s))
            db.session.commit()
            print(f"  ✅ Stores seeded.")

        # Pre-generate recommendations
        from ml.recommendation_engine import cache_recommendations_for_user
        cache_recommendations_for_user(student1.id)
        cache_recommendations_for_user(student2.id)
        print("  ✅ Static recommendations generated.")

        print("\n🎉 Database seeding complete!")
        print(f"   Student 1 (Good): {student1_email} / {password}")
        print(f"   Student 2 (Bad):  {student2_email} / {password}")
        print(f"   Parent:           {parent_email} / {password}")

    # ─── Train ML model (outside app context) ────────────────────────
    print("\n🤖 Training ML category classifier (Warming up AI)...")
    try:
        from ml.train_category_model import train_model
        train_model()
        print("  ✅ ML model trained and saved.")
    except Exception as exc:
        print(f"  ⚠️  ML training failed: {exc}")

if __name__ == '__main__':
    seed()
