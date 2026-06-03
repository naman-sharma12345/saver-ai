"""
Analytics routes – spending insights, financial health, and spending prediction.
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from models import Expense, Budget

analytics_bp = Blueprint('analytics', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/spending-by-category?month=YYYY-MM
# ─────────────────────────────────────────────────────────────────────────────
@analytics_bp.route('/analytics/spending-by-category', methods=['GET'])
@jwt_required()
def spending_by_category():
    """Return total spending per category for a given month, with percentages."""
    user_id = int(get_jwt_identity())
    month = request.args.get('month')

    query = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count'),
    ).filter(Expense.user_id == user_id)

    if month:
        try:
            year, mon = month.split('-')
            start = datetime(int(year), int(mon), 1, tzinfo=timezone.utc)
            if int(mon) == 12:
                end = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(int(year), int(mon) + 1, 1, tzinfo=timezone.utc)
            query = query.filter(Expense.created_at >= start, Expense.created_at < end)
        except (ValueError, IndexError):
            return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

    results = query.group_by(Expense.category).all()

    grand_total = sum(r.total for r in results) or 1  # avoid division by zero

    breakdown = []
    for r in results:
        breakdown.append({
            'category': r.category,
            'total': round(r.total, 2),
            'count': r.count,
            'percentage': round((r.total / grand_total) * 100, 2),
        })

    # Sort by total descending
    breakdown.sort(key=lambda x: x['total'], reverse=True)

    return jsonify({
        'month': month,
        'grand_total': round(grand_total, 2),
        'breakdown': breakdown,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/spending-over-time?months=6
# ─────────────────────────────────────────────────────────────────────────────
@analytics_bp.route('/analytics/spending-over-time', methods=['GET'])
@jwt_required()
def spending_over_time():
    """Return monthly totals for a line chart (last N months)."""
    user_id = int(get_jwt_identity())
    num_months = request.args.get('months', 6, type=int)
    num_months = min(max(num_months, 1), 24)  # clamp 1–24

    now = datetime.now(timezone.utc)

    # Build month boundaries
    monthly_data = []
    for i in range(num_months - 1, -1, -1):
        # Compute target year/month
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

        monthly_data.append({
            'month': f"{target_year}-{target_month:02d}",
            'total': round(total, 2),
        })

    return jsonify({'spending_over_time': monthly_data}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/budget-vs-actual?month=YYYY-MM
# ─────────────────────────────────────────────────────────────────────────────
@analytics_bp.route('/analytics/budget-vs-actual', methods=['GET'])
@jwt_required()
def budget_vs_actual():
    """Compare budget limits vs actual spending per category for a month."""
    user_id = int(get_jwt_identity())
    month = request.args.get('month')

    if not month:
        return jsonify({'error': 'month query parameter is required (YYYY-MM)'}), 400

    try:
        year, mon = month.split('-')
        month_date = datetime.strptime(month, '%Y-%m').date()
        start = datetime(int(year), int(mon), 1, tzinfo=timezone.utc)
        if int(mon) == 12:
            end = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(int(year), int(mon) + 1, 1, tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

    # Budgets for this month
    budgets = Budget.query.filter_by(user_id=user_id, month=month_date).all()
    budget_map = {b.category: b.budget_limit for b in budgets}

    # Actual spending
    actuals = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
    ).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at < end,
    ).group_by(Expense.category).all()

    actual_map = {a.category: round(a.total, 2) for a in actuals}

    # Merge categories
    all_categories = set(list(budget_map.keys()) + list(actual_map.keys()))
    comparison = []
    for cat in sorted(all_categories):
        budget_limit = budget_map.get(cat, 0.0)
        actual = actual_map.get(cat, 0.0)
        comparison.append({
            'category': cat,
            'budget_limit': budget_limit,
            'actual': actual,
            'remaining': round(budget_limit - actual, 2),
            'over_budget': actual > budget_limit if budget_limit > 0 else False,
        })

    return jsonify({
        'month': month,
        'comparison': comparison,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/financial-health-score
# ─────────────────────────────────────────────────────────────────────────────
@analytics_bp.route('/analytics/financial-health-score', methods=['GET'])
@jwt_required()
def financial_health_score():
    """
    Compute a financial health score (0–100) with detailed breakdown.
    Uses ML-powered health score module.
    """
    user_id = int(get_jwt_identity())
    from ml.health_score import compute_financial_health
    result = compute_financial_health(user_id)

    if 'error' in result:
        return jsonify(result), 404

    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/next-month-prediction
# ─────────────────────────────────────────────────────────────────────────────
@analytics_bp.route('/analytics/next-month-prediction', methods=['GET'])
@jwt_required()
def next_month_prediction():
    """
    Predict total spending for next month using linear regression
    on the user's historical monthly totals.
    """
    user_id = int(get_jwt_identity())
    from ml.spending_predictor import predict_next_month_spending
    result = predict_next_month_spending(user_id)
    return jsonify(result), 200
