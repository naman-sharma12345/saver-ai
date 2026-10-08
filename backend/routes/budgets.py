"""
Budget CRUD routes.
GET    /api/budgets          – list budgets for current user
POST   /api/budgets          – create a budget
PUT    /api/budgets/<id>     – update a budget
DELETE /api/budgets/<id>     – delete a budget
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import Budget, Expense
from ml.budget_pace import budget_pace

budgets_bp = Blueprint('budgets', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/budgets
# ─────────────────────────────────────────────────────────────────────────────
@budgets_bp.route('/budgets', methods=['GET'])
@jwt_required()
def list_budgets():
    """Return all budgets for the current user, optionally filtered by month."""
    user_id = int(get_jwt_identity())
    query = Budget.query.filter_by(user_id=user_id)

    month = request.args.get('month')  # YYYY-MM
    if month:
        try:
            dt = datetime.strptime(month, '%Y-%m').date()
            query = query.filter_by(month=dt)
        except ValueError:
            return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

    budgets = query.order_by(Budget.month.desc(), Budget.category).all()
    return jsonify({'budgets': [b.to_dict() for b in budgets]}), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/budgets
# ─────────────────────────────────────────────────────────────────────────────
@budgets_bp.route('/budgets', methods=['POST'])
@jwt_required()
def create_budget():
    """
    Create a monthly budget for a category.
    Required: category, budget_limit, month (YYYY-MM).
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['category', 'budget_limit', 'month']
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        budget_limit = float(data['budget_limit'])
    except (ValueError, TypeError):
        return jsonify({'error': 'budget_limit must be a number'}), 400

    if budget_limit <= 0:
        return jsonify({'error': 'budget_limit must be positive'}), 400

    try:
        month_date = datetime.strptime(data['month'], '%Y-%m').date()
    except ValueError:
        return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

    category = str(data['category']).strip()

    # Prevent duplicate budget for same user/category/month
    existing = Budget.query.filter_by(
        user_id=user_id, category=category, month=month_date
    ).first()
    if existing:
        return jsonify({'error': 'Budget already exists for this category and month. Use PUT to update.'}), 409

    budget = Budget(
        user_id=user_id,
        category=category,
        budget_limit=budget_limit,
        month=month_date,
    )
    db.session.add(budget)
    db.session.commit()

    return jsonify({
        'message': 'Budget created successfully',
        'budget': budget.to_dict(),
    }), 201


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/budgets/<id>
# ─────────────────────────────────────────────────────────────────────────────
@budgets_bp.route('/budgets/<int:budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    """Update an existing budget's limit or category."""
    user_id = int(get_jwt_identity())
    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
    if budget is None:
        return jsonify({'error': 'Budget not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'budget_limit' in data:
        try:
            budget.budget_limit = float(data['budget_limit'])
        except (ValueError, TypeError):
            return jsonify({'error': 'budget_limit must be a number'}), 400

    if 'category' in data:
        budget.category = str(data['category']).strip()

    if 'month' in data:
        try:
            budget.month = datetime.strptime(data['month'], '%Y-%m').date()
        except ValueError:
            return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

    db.session.commit()

    return jsonify({
        'message': 'Budget updated successfully',
        'budget': budget.to_dict(),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/budgets/<id>
# ─────────────────────────────────────────────────────────────────────────────
@budgets_bp.route('/budgets/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    """Delete a budget entry."""
    user_id = int(get_jwt_identity())
    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
    if budget is None:
        return jsonify({'error': 'Budget not found'}), 404

    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted successfully'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/budgets/pace  – will each budget last the month? (free for everyone)
# ─────────────────────────────────────────────────────────────────────────────
@budgets_bp.route('/budgets/pace', methods=['GET'])
@jwt_required()
def budgets_pace():
    user_id = int(get_jwt_identity())
    today = datetime.now().date()
    first = today.replace(day=1)
    budgets = Budget.query.filter_by(user_id=user_id, month=first).all()
    spent = {}
    for e in Expense.query.filter(Expense.user_id == user_id, Expense.created_at >= datetime(first.year, first.month, 1)).all():
        spent[e.category] = spent.get(e.category, 0.0) + e.amount
    return jsonify(budget_pace([{'category': b.category, 'budget_limit': b.budget_limit} for b in budgets], spent, today)), 200
