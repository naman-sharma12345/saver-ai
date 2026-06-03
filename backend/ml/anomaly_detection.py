"""
Anomaly detection for unusual spending.

Uses Isolation Forest on a user's expense amounts (and day-of-month)
to flag statistical outliers.

Usage (within Flask app context):
    from ml.anomaly_detection import detect_anomalies
    anomaly_ids = detect_anomalies(user_id=1)
"""

import logging
from datetime import datetime, timezone

import numpy as np
from sklearn.ensemble import IsolationForest

from app import db
from models import Expense

logger = logging.getLogger(__name__)


def detect_anomalies(user_id: int, contamination: float = 0.1) -> list[dict]:
    """
    Detect anomalous expenses for a user using Isolation Forest.

    Features used:
        - amount
        - day_of_month
        - hour_of_day

    Args:
        user_id: The user to analyse.
        contamination: Expected proportion of outliers (default 10%).

    Returns:
        List of dicts with expense details and anomaly explanation.
    """
    expenses = Expense.query.filter_by(user_id=user_id).order_by(
        Expense.created_at.desc()
    ).all()

    if len(expenses) < 5:
        logger.info("User %d has fewer than 5 expenses — skipping anomaly detection.", user_id)
        return []

    # Build feature matrix
    amounts = []
    days = []
    hours = []
    expense_map = {}

    for exp in expenses:
        amounts.append(exp.amount)
        dt = exp.created_at or datetime.now(timezone.utc)
        days.append(dt.day)
        hours.append(dt.hour)
        expense_map[len(amounts) - 1] = exp

    X = np.column_stack([amounts, days, hours])

    # Normalise features for better isolation forest performance
    X_norm = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)

    # Fit Isolation Forest
    clf = IsolationForest(
        contamination=min(contamination, 0.5),
        random_state=42,
        n_estimators=100,
    )
    predictions = clf.fit_predict(X_norm)
    scores = clf.decision_function(X_norm)

    # Collect anomalies (predictions == -1)
    anomalies = []
    mean_amount = np.mean(amounts)
    std_amount = np.std(amounts) if np.std(amounts) > 0 else 1.0

    for idx, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:
            exp = expense_map[idx]
            deviation = (exp.amount - mean_amount) / std_amount

            # Build explanation
            if exp.amount > mean_amount + 2 * std_amount:
                explanation = (
                    f"This expense of ₹{exp.amount:.0f} is unusually HIGH — "
                    f"it's {deviation:.1f}x standard deviations above your "
                    f"average of ₹{mean_amount:.0f}."
                )
            elif exp.amount < mean_amount - 2 * std_amount:
                explanation = (
                    f"This expense of ₹{exp.amount:.0f} is unusually LOW — "
                    f"it's {abs(deviation):.1f}x standard deviations below your "
                    f"average of ₹{mean_amount:.0f}."
                )
            else:
                explanation = (
                    f"This expense of ₹{exp.amount:.0f} on day {exp.created_at.day} "
                    f"has an unusual pattern compared to your spending habits."
                )

            anomalies.append({
                'expense_id': exp.id,
                'expense': exp.to_dict(),
                'anomaly_score': round(float(score), 4),
                'explanation': explanation,
            })

    # Sort by severity (most anomalous first — lower score = more anomalous)
    anomalies.sort(key=lambda x: x['anomaly_score'])

    return anomalies


def flag_anomalies_in_db(user_id: int) -> int:
    """
    Run anomaly detection and set is_anomaly=True on flagged expenses.
    Returns the number of anomalies flagged.
    """
    # First, reset all anomaly flags for this user
    try:
        Expense.query.filter_by(user_id=user_id).update({'is_anomaly': False})
    except Exception:
        # is_anomaly column might not exist yet
        db.session.rollback()
        return 0

    anomalies = detect_anomalies(user_id)

    for a in anomalies:
        exp = Expense.query.get(a['expense_id'])
        if exp:
            exp.is_anomaly = True

    db.session.commit()
    logger.info("Flagged %d anomalies for user %d", len(anomalies), user_id)
    return len(anomalies)
