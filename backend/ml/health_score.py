"""
Financial health score calculator.

Produces a composite score (0-100) broken down into:
  - Savings Score    (0-40)  — allowance vs average monthly spend
  - Budget Score     (0-30)  — how many categories are within budget
  - Discipline Score (0-30)  — anomaly frequency + spending consistency

Usage (within Flask app context):
    from ml.health_score import compute_financial_health
    result = compute_financial_health(user_id=1)
"""

import logging
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import func

from app import db
from models import Expense, Budget, User

logger = logging.getLogger(__name__)


def _month_bounds(dt=None):
    now = dt or datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _past_monthly_totals(user_id: int, n_months: int = 6):
    """Get monthly spending totals for the past n months."""
    now = datetime.now(timezone.utc)
    totals = []
    for i in range(n_months):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        if m == 12:
            end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(y, m + 1, 1, tzinfo=timezone.utc)
        total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.created_at >= start,
            Expense.created_at < end,
        ).scalar() or 0.0
        totals.append(float(total))
    return totals


def compute_financial_health(user_id: int) -> dict:
    """
    Compute a 0-100 financial health score with breakdown.

    Returns:
        {
            "score": int,
            "breakdown": {
                "savings":    {"score": int, "max": 40, "details": str},
                "budget":     {"score": int, "max": 30, "details": str},
                "discipline": {"score": int, "max": 30, "details": str},
            },
            "total_spending": float,
            "monthly_allowance": float,
            "tips": [str],
        }
    """
    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found'}

    start, end = _month_bounds()
    allowance = user.monthly_allowance or 1.0

    # Current month total
    total_spending = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at < end,
    ).scalar() or 0.0

    tips = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. SAVINGS SCORE (0 - 40)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    spending_ratio = total_spending / allowance
    if spending_ratio <= 0.5:
        savings_score = 40
        savings_detail = f"Excellent! Only {spending_ratio*100:.0f}% of allowance used."
    elif spending_ratio <= 0.7:
        savings_score = 32
        savings_detail = f"Good — {spending_ratio*100:.0f}% used. Room for improvement."
    elif spending_ratio <= 0.85:
        savings_score = 22
        savings_detail = f"Moderate — {spending_ratio*100:.0f}% used. Watch your spending."
        tips.append("Try to keep spending below 70% of your allowance.")
    elif spending_ratio <= 1.0:
        savings_score = 12
        savings_detail = f"High — {spending_ratio*100:.0f}% used. Very little savings."
        tips.append("You're close to exhausting your allowance. Cut discretionary expenses.")
    else:
        savings_score = 0
        savings_detail = f"Over-budget! {spending_ratio*100:.0f}% of allowance spent."
        tips.append("You've exceeded your monthly allowance!")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. BUDGET SCORE (0 - 30)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    budgets = Budget.query.filter_by(user_id=user_id, month=start.date()).all()

    if budgets:
        within_budget = 0
        over_budget_cats = []
        for b in budgets:
            actual = db.session.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.category == b.category,
                Expense.created_at >= start,
                Expense.created_at < end,
            ).scalar() or 0.0
            if actual <= b.budget_limit:
                within_budget += 1
            else:
                over_budget_cats.append(b.category)

        adherence = within_budget / len(budgets)
        budget_score = round(adherence * 30)
        budget_detail = (
            f"{within_budget}/{len(budgets)} categories within budget "
            f"({adherence*100:.0f}% adherence)."
        )
        if over_budget_cats:
            tips.append(
                f"Over budget in: {', '.join(over_budget_cats)}. "
                f"Review these categories."
            )
    else:
        budget_score = 10  # partial credit for tracking expenses
        budget_detail = "No budgets set. Set budgets to improve this score."
        tips.append("Set monthly budgets per category to improve your score by up to 20 points.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. DISCIPLINE SCORE (0 - 30)
    #    - Anomaly frequency  (0-15)
    #    - Spending consistency / coefficient of variation (0-15)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 3a. Anomaly penalty (check is_anomaly field if it exists)
    anomaly_count = 0
    try:
        anomaly_count = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.created_at >= start,
            Expense.created_at < end,
            Expense.is_anomaly == True,  # noqa: E712
        ).count()
    except Exception:
        pass  # Field might not exist yet

    total_expenses_count = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at < end,
    ).count()

    if total_expenses_count > 0:
        anomaly_rate = anomaly_count / total_expenses_count
        anomaly_score = max(0, round(15 * (1 - anomaly_rate * 5)))  # heavy penalty
    else:
        anomaly_score = 15

    if anomaly_count > 0:
        tips.append(
            f"{anomaly_count} unusual expenses detected this month. "
            f"Review them in the Anomalies section."
        )

    # 3b. Spending consistency (CoV of past monthly totals)
    past_totals = _past_monthly_totals(user_id, 6)
    non_zero_totals = [t for t in past_totals if t > 0]

    if len(non_zero_totals) >= 2:
        arr = np.array(non_zero_totals)
        cv = float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 0
        if cv < 0.2:
            consistency_score = 15
            consistency_detail = "Very consistent"
        elif cv < 0.4:
            consistency_score = 11
            consistency_detail = "Mostly consistent"
        elif cv < 0.6:
            consistency_score = 7
            consistency_detail = "Somewhat variable"
        else:
            consistency_score = 3
            consistency_detail = "Highly variable"
            tips.append("Your spending varies a lot month-to-month. Try to stabilise.")
    else:
        consistency_score = 8
        consistency_detail = "Not enough data"

    discipline_score = anomaly_score + consistency_score
    discipline_detail = (
        f"Anomalies: {anomaly_count} detected (score {anomaly_score}/15). "
        f"Consistency: {consistency_detail} (score {consistency_score}/15)."
    )

    # ── Composite ────────────────────────────────────────────────────────
    total_score = savings_score + budget_score + discipline_score
    total_score = max(0, min(100, total_score))

    return {
        'score': total_score,
        'breakdown': {
            'savings': {
                'score': savings_score,
                'max': 40,
                'details': savings_detail,
            },
            'budget': {
                'score': budget_score,
                'max': 30,
                'details': budget_detail,
            },
            'discipline': {
                'score': discipline_score,
                'max': 30,
                'details': discipline_detail,
            },
        },
        'total_spending': round(total_spending, 2),
        'monthly_allowance': allowance,
        'spending_ratio': round(spending_ratio * 100, 2),
        'tips': tips,
    }
