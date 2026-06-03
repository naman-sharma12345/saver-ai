"""
Monthly spending predictor.

Predicts a user's total spending for the next month using linear
regression on their historical monthly totals.  Falls back to the
global average across all students when insufficient data exists.

Usage (within Flask app context):
    from ml.spending_predictor import predict_next_month_spending
    result = predict_next_month_spending(user_id=1)
"""

import logging
from datetime import datetime, timezone

import numpy as np
from sklearn.linear_model import LinearRegression

from app import db
from models import Expense, User
from sqlalchemy import func

logger = logging.getLogger(__name__)


def _get_monthly_totals(user_id: int, max_months: int = 12) -> list[dict]:
    """Aggregate expenses by month for a user, most recent first."""
    now = datetime.now(timezone.utc)
    monthly = []

    for i in range(max_months - 1, -1, -1):
        target_month = now.month - i
        target_year = now.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        start = datetime(target_year, target_month, 1, tzinfo=timezone.utc)
        if target_month == 12:
            end = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(target_year, target_month + 1, 1, tzinfo=timezone.utc)

        total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.created_at >= start,
            Expense.created_at < end,
        ).scalar() or 0.0

        if total > 0:
            monthly.append({
                'year': target_year,
                'month': target_month,
                'index': len(monthly),
                'total': float(total),
            })

    return monthly


def _global_average_monthly() -> float:
    """Compute the average monthly spending across all students."""
    now = datetime.now(timezone.utc)
    # Last 3 months global average
    totals = []
    for i in range(3):
        target_month = now.month - i
        target_year = now.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        start = datetime(target_year, target_month, 1, tzinfo=timezone.utc)
        if target_month == 12:
            end = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(target_year, target_month + 1, 1, tzinfo=timezone.utc)

        total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.created_at >= start,
            Expense.created_at < end,
        ).scalar() or 0.0
        if total > 0:
            totals.append(total)

    if totals:
        n_students = User.query.filter_by(role='student').count() or 1
        return sum(totals) / len(totals) / n_students

    return 0.0


def predict_next_month_spending(user_id: int) -> dict:
    """
    Predict total spending for the next month.

    Returns:
        {
            "predicted_amount": float,
            "confidence_interval": {"lower": float, "upper": float},
            "method": "linear_regression" | "global_average" | "insufficient_data",
            "monthly_history": [...],
            "std_error": float,
        }
    """
    monthly = _get_monthly_totals(user_id, max_months=12)

    # Need at least 3 data points for linear regression
    if len(monthly) >= 3:
        X = np.array([m['index'] for m in monthly]).reshape(-1, 1)
        y = np.array([m['total'] for m in monthly])

        model = LinearRegression()
        model.fit(X, y)

        next_idx = len(monthly)
        predicted = float(model.predict([[next_idx]])[0])

        # Residual std error
        residuals = y - model.predict(X).flatten()
        std_error = float(np.std(residuals))

        # Don't predict negative
        predicted = max(predicted, 0.0)

        return {
            'predicted_amount': round(predicted, 2),
            'confidence_interval': {
                'lower': round(max(predicted - 1.96 * std_error, 0), 2),
                'upper': round(predicted + 1.96 * std_error, 2),
            },
            'method': 'linear_regression',
            'monthly_history': monthly,
            'std_error': round(std_error, 2),
            'trend': 'increasing' if model.coef_[0] > 50 else (
                'decreasing' if model.coef_[0] < -50 else 'stable'
            ),
            'slope_per_month': round(float(model.coef_[0]), 2),
        }

    # Fallback: global average
    global_avg = _global_average_monthly()
    if global_avg > 0:
        return {
            'predicted_amount': round(global_avg, 2),
            'confidence_interval': {
                'lower': round(global_avg * 0.7, 2),
                'upper': round(global_avg * 1.3, 2),
            },
            'method': 'global_average',
            'monthly_history': monthly,
            'std_error': round(global_avg * 0.3, 2),
            'trend': 'unknown',
            'slope_per_month': 0.0,
        }

    return {
        'predicted_amount': 0.0,
        'confidence_interval': {'lower': 0.0, 'upper': 0.0},
        'method': 'insufficient_data',
        'monthly_history': monthly,
        'std_error': 0.0,
        'trend': 'unknown',
        'slope_per_month': 0.0,
    }
