"""
Budget & saving recommendation engine.

Analyses spending vs budgets, detects over-spending, suggests
cheaper store alternatives, and provides personal finance tips.

Usage (within Flask app context):
    from ml.recommendation_engine import generate_recommendations
    recs = generate_recommendations(user_id=1)
"""

import random
import logging
from datetime import datetime, timezone, date

from sqlalchemy import func
from geopy.distance import geodesic

from app import db
from models import Expense, Budget, User, Store, SavingRecommendation

logger = logging.getLogger(__name__)

# ─── General finance tips pool ───────────────────────────────────────────────
_GENERAL_TIPS = [
    ("Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings.", 0),
    ("Track every expense — even small ones add up over the month.", 0),
    ("Set up an emergency fund equal to 3 months of expenses.", 0),
    ("Use UPI cashback offers when paying to save 2-5% on purchases.", 0),
    ("Carry a water bottle to campus — small beverage purchases add up to ₹500+/month.", 500),
    ("Cook one meal a day at home to save ₹2000-3000 monthly.", 2500),
    ("Use student discounts — many apps offer 20-50% off for .edu emails.", 0),
    ("Cancel unused subscriptions — review all recurring charges monthly.", 300),
    ("Buy second-hand textbooks or use the library to save ₹1000+/semester.", 1000),
    ("Share streaming subscriptions with 3-4 friends to cut costs by 75%.", 400),
    ("Walk or cycle for distances under 2 km instead of taking autos.", 800),
    ("Plan meals weekly to avoid impulse food ordering.", 1500),
    ("Use the college gym instead of expensive gym memberships.", 1000),
    ("Always compare prices on at least 2 apps before buying online.", 0),
    ("Set spending alerts in your banking app at 80% of your budget.", 0),
]


def _month_bounds(dt: datetime | None = None):
    """Return (start, end) datetime for the current month."""
    now = dt or datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _cat_totals(user_id: int, start, end):
    """Category-wise spending totals for a date range."""
    rows = db.session.query(
        Expense.category, func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at < end,
    ).group_by(Expense.category).all()
    return {r.category: float(r.total) for r in rows}


def _find_cheaper_stores(category: str, current_price_level: int,
                         lat: float, lng: float, radius_km: float = 5.0) -> list[dict]:
    """Find stores in the same category with lower price levels within radius."""
    stores = Store.query.filter(
        Store.category.ilike(f'%{category}%'),
        Store.average_price_level < current_price_level,
    ).all()

    results = []
    user_loc = (lat, lng)
    for s in stores:
        try:
            dist = geodesic(user_loc, (s.lat, s.lng)).km
        except Exception:
            continue
        if dist <= radius_km:
            results.append({
                'store': s.to_dict(),
                'distance_km': round(dist, 2),
                'price_level_diff': current_price_level - s.average_price_level,
            })

    results.sort(key=lambda x: (x['distance_km'], -x['price_level_diff']))
    return results[:3]


def _store_based_tips(user_id: int, start, end) -> list[dict]:
    """
    For recent expenses with location data, suggest cheaper alternatives.
    """
    tips = []
    recent = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at < end,
        Expense.location_lat.isnot(None),
        Expense.location_lng.isnot(None),
    ).order_by(Expense.created_at.desc()).limit(10).all()

    seen_categories = set()
    for exp in recent:
        if exp.category in seen_categories:
            continue

        # Find the store's price level (approximate from stores table)
        matched_store = Store.query.filter(
            Store.name.ilike(f'%{exp.store_name}%')
        ).first()
        current_level = matched_store.average_price_level if matched_store else 3

        if current_level >= 3:
            cheaper = _find_cheaper_stores(
                exp.category, current_level,
                exp.location_lat, exp.location_lng,
            )
            if cheaper:
                alt = cheaper[0]
                savings_pct = alt['price_level_diff'] * 7.5  # ~7.5% per level
                est_saving = round(exp.amount * savings_pct / 100, 2)
                tips.append({
                    'recommendation_text': (
                        f"Next time, buy your {exp.category.lower()} from "
                        f"'{alt['store']['name']}' ({alt['distance_km']} km away) "
                        f"instead of '{exp.store_name}' to save ~₹{est_saving:.0f}."
                    ),
                    'amount_saved': est_saving,
                })
                seen_categories.add(exp.category)

    return tips


def generate_recommendations(user_id: int) -> list[dict]:
    """
    Generate comprehensive saving recommendations for a user.

    Returns list of {recommendation_text: str, amount_saved: float}.
    """
    user = User.query.get(user_id)
    if not user:
        return []

    start, end = _month_bounds()
    cat_spending = _cat_totals(user_id, start, end)
    total_spending = sum(cat_spending.values()) or 0.0
    allowance = user.monthly_allowance or 0.0

    recs = []

    # ── 1. Budget overrun analysis ───────────────────────────────────────
    budgets = Budget.query.filter_by(user_id=user_id, month=start.date()).all()
    for b in budgets:
        actual = cat_spending.get(b.category, 0.0)
        if actual > b.budget_limit:
            over_pct = ((actual - b.budget_limit) / b.budget_limit) * 100
            saving = round(actual - b.budget_limit, 2)

            if b.category == 'Food':
                tip = (
                    f"You've spent {over_pct:.0f}% over your {b.category} budget "
                    f"(₹{actual:.0f}/₹{b.budget_limit:.0f}). "
                    f"Try cooking at home 2 extra days a week to save ₹{saving:.0f}."
                )
            elif b.category == 'Transport':
                tip = (
                    f"Transport spending is {over_pct:.0f}% over budget "
                    f"(₹{actual:.0f}/₹{b.budget_limit:.0f}). "
                    f"Use metro or carpool to save ₹{saving:.0f}."
                )
            elif b.category == 'Entertainment':
                tip = (
                    f"Entertainment is {over_pct:.0f}% over budget "
                    f"(₹{actual:.0f}/₹{b.budget_limit:.0f}). "
                    f"Try free campus events or movie nights at home to save ₹{saving:.0f}."
                )
            elif b.category == 'Shopping':
                tip = (
                    f"Shopping spending is {over_pct:.0f}% over budget "
                    f"(₹{actual:.0f}/₹{b.budget_limit:.0f}). "
                    f"Apply the 48-hour rule before impulse purchases to save ₹{saving:.0f}."
                )
            else:
                tip = (
                    f"You've spent {over_pct:.0f}% over your {b.category} budget "
                    f"(₹{actual:.0f}/₹{b.budget_limit:.0f}). "
                    f"Try to cut back ₹{saving:.0f} this month."
                )

            recs.append({'recommendation_text': tip, 'amount_saved': saving})

    # ── 2. High discretionary spending ───────────────────────────────────
    discretionary = ['Entertainment', 'Shopping']
    disc_total = sum(cat_spending.get(c, 0) for c in discretionary)
    if total_spending > 0 and disc_total / total_spending > 0.35:
        pct = disc_total / total_spending * 100
        target_saving = round(disc_total * 0.3, 2)
        recs.append({
            'recommendation_text': (
                f"Discretionary spending (Entertainment + Shopping) is {pct:.0f}% "
                f"of your total. Set a savings goal of ₹{target_saving:.0f} by "
                f"reducing non-essential purchases."
            ),
            'amount_saved': target_saving,
        })

    # ── 3. Overall allowance warning ─────────────────────────────────────
    if allowance > 0:
        ratio = total_spending / allowance
        if ratio > 0.9:
            recs.append({
                'recommendation_text': (
                    f"⚠️ You've used {ratio*100:.0f}% of your ₹{allowance:.0f} "
                    f"allowance (₹{total_spending:.0f} spent). Tighten spending "
                    f"for the rest of the month."
                ),
                'amount_saved': round(total_spending - allowance * 0.7, 2),
            })
        elif ratio > 0.7:
            recs.append({
                'recommendation_text': (
                    f"You've used {ratio*100:.0f}% of your allowance. "
                    f"Aim to keep it under 80% to build savings."
                ),
                'amount_saved': round(total_spending * 0.1, 2),
            })

    # ── 4. Store-based cheaper alternatives ──────────────────────────────
    store_tips = _store_based_tips(user_id, start, end)
    recs.extend(store_tips)

    # ── 5. Category-specific advice ──────────────────────────────────────
    food_total = cat_spending.get('Food', 0)
    if food_total > 3000:
        recs.append({
            'recommendation_text': (
                f"Food spending is ₹{food_total:.0f}. Use the college mess "
                f"and meal-prep on weekends to save 25-30%."
            ),
            'amount_saved': round(food_total * 0.25, 2),
        })

    transport_total = cat_spending.get('Transport', 0)
    if transport_total > 2000:
        recs.append({
            'recommendation_text': (
                f"Transport costs are ₹{transport_total:.0f}. "
                f"Get a monthly metro pass (₹750) instead of daily tickets."
            ),
            'amount_saved': round(transport_total * 0.35, 2),
        })

    # ── 6. No budgets set ────────────────────────────────────────────────
    if not budgets and total_spending > 0:
        recs.append({
            'recommendation_text': (
                "You haven't set any budgets. Students who budget save 15-20% more. "
                "Set budgets for each category from the Budgets page."
            ),
            'amount_saved': round(total_spending * 0.15, 2),
        })

    # ── 7. Sprinkle general tips ─────────────────────────────────────────
    random.seed(datetime.now().day)  # deterministic per day
    selected = random.sample(_GENERAL_TIPS, min(2, len(_GENERAL_TIPS)))
    for tip_text, amt in selected:
        recs.append({
            'recommendation_text': f"💡 Tip: {tip_text}",
            'amount_saved': amt,
        })

    # ── 8. Positive reinforcement if doing well ──────────────────────────
    if not recs or (allowance > 0 and total_spending < allowance * 0.5):
        recs.append({
            'recommendation_text': (
                "🌟 Great job! You're spending less than 50% of your allowance. "
                "Keep it up and consider investing the surplus."
            ),
            'amount_saved': 0,
        })

    return recs


def cache_recommendations_for_user(user_id: int) -> list[dict]:
    """
    Generate recommendations and cache them in the database.
    If today's recommendations already exist, return the cached version.
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_end = today_start.replace(hour=23, minute=59, second=59)

    cached = SavingRecommendation.query.filter(
        SavingRecommendation.user_id == user_id,
        SavingRecommendation.created_at >= today_start,
        SavingRecommendation.created_at <= today_end,
    ).all()

    if cached:
        return [r.to_dict() for r in cached]

    # Generate fresh
    recs = generate_recommendations(user_id)

    saved = []
    for rec in recs:
        sr = SavingRecommendation(
            user_id=user_id,
            recommendation_text=rec['recommendation_text'],
            amount_saved=rec.get('amount_saved', 0),
        )
        db.session.add(sr)
        saved.append(sr)

    db.session.commit()
    return [s.to_dict() for s in saved]


def generate_daily_recommendations_all_users():
    """
    Scheduled job: generate recommendations for every student.
    Called by APScheduler at midnight.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        students = User.query.filter_by(role='student').all()
        logger.info("Generating daily recommendations for %d students", len(students))
        for student in students:
            try:
                cache_recommendations_for_user(student.id)
            except Exception as exc:
                logger.error("Failed for user %d: %s", student.id, exc)
        logger.info("Daily recommendation generation complete.")
