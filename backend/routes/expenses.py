"""
Expense CRUD routes.
POST   /api/expenses           – create (with ML auto-categorisation)
GET    /api/expenses            – list with filters
GET    /api/expenses/anomalies  – flagged anomalous expenses
GET    /api/expenses/<id>       – single expense
PUT    /api/expenses/<id>       – update
DELETE /api/expenses/<id>       – delete
"""

import math
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import Expense
from ml.categorizer import predict_category
from ml.anomaly_detection import detect_anomalies, flag_anomalies_in_db

expenses_bp = Blueprint('expenses', __name__)


def _parse_amount(value):
    """Return a positive finite float, or None if the value is not valid."""
    if isinstance(value, bool):
        return None
    try:
        amount = float(value)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(amount) or amount <= 0:
        return None
    return amount


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/expenses
# ─────────────────────────────────────────────────────────────────────────────
@expenses_bp.route('/expenses', methods=['POST'])
@jwt_required()
def create_expense():
    """
    Create a new expense.
    Required: amount, description, store_name.
    Optional: category (auto-detected via ML if omitted), lat, lng, is_recurring.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    required = ['amount', 'description', 'store_name']
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    amount = _parse_amount(data['amount'])
    if amount is None:
        return jsonify({'error': 'amount must be a positive number'}), 400

    description = str(data['description']).strip()
    store_name = str(data['store_name']).strip()

    # Auto-categorise via ML if category not provided
    category = data.get('category', '').strip()
    ml_info = None
    if not category:
        result = predict_category(description, store_name)
        category = result['category']
        ml_info = {
            'predicted_category': result['category'],
            'confidence': result['confidence'],
            'method': result['method'],
        }

    expense = Expense(
        user_id=user_id,
        amount=amount,
        category=category,
        description=description,
        store_name=store_name,
        location_lat=data.get('location_lat') or data.get('lat'),
        location_lng=data.get('location_lng') or data.get('lng'),
        is_recurring=bool(data.get('is_recurring', False)),
    )
    db.session.add(expense)
    db.session.commit()

    response = {
        'message': 'Expense created successfully',
        'expense': expense.to_dict(),
    }
    if ml_info:
        response['categorization'] = ml_info

    return jsonify(response), 201


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/expenses
# ─────────────────────────────────────────────────────────────────────────────
@expenses_bp.route('/expenses', methods=['GET'])
@jwt_required()
def list_expenses():
    """
    List expenses for the current user.
    Query params:  category, month (YYYY-MM), start_date, end_date, page, per_page.
    """
    user_id = int(get_jwt_identity())
    query = Expense.query.filter_by(user_id=user_id)

    # ── Filters ──────────────────────────────────────────────────────────
    category = request.args.get('category')
    if category:
        query = query.filter(Expense.category.ilike(category))

    month = request.args.get('month')  # YYYY-MM
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

    start_date = request.args.get('start_date')
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            query = query.filter(Expense.created_at >= sd)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400

    end_date = request.args.get('end_date')
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            query = query.filter(Expense.created_at <= ed)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400

    # ── Pagination ───────────────────────────────────────────────────────
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    page = max(page or 1, 1)
    per_page = min(max(per_page or 50, 1), 100)

    query = query.order_by(Expense.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'expenses': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/expenses/anomalies
# ─────────────────────────────────────────────────────────────────────────────
@expenses_bp.route('/expenses/anomalies', methods=['GET'])
@jwt_required()
def get_anomalies():
    """
    Detect and return anomalous expenses for the current user.
    Uses Isolation Forest on expense amounts and timing.
    """
    user_id = int(get_jwt_identity())

    # Flag anomalies in the database
    try:
        count = flag_anomalies_in_db(user_id)
    except Exception:
        count = 0

    # Detect and return details
    anomalies = detect_anomalies(user_id)

    return jsonify({
        'anomalies': anomalies,
        'total': len(anomalies),
        'flagged_in_db': count,
        'message': (
            f'{len(anomalies)} unusual expenses detected.'
            if anomalies else
            'No anomalies detected — your spending looks normal!'
        ),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/expenses/<id>
# ─────────────────────────────────────────────────────────────────────────────
@expenses_bp.route('/expenses/<int:expense_id>', methods=['GET'])
@jwt_required()
def get_expense(expense_id):
    """Return a single expense owned by the current user."""
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if expense is None:
        return jsonify({'error': 'Expense not found'}), 404
    return jsonify({'expense': expense.to_dict()}), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/expenses/<id>
# ─────────────────────────────────────────────────────────────────────────────
@expenses_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """Update an existing expense."""
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if expense is None:
        return jsonify({'error': 'Expense not found'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'amount' in data:
        amount = _parse_amount(data['amount'])
        if amount is None:
            return jsonify({'error': 'amount must be a positive number'}), 400
        expense.amount = amount

    if 'category' in data:
        expense.category = str(data['category']).strip()
    if 'description' in data:
        expense.description = str(data['description']).strip()
    if 'store_name' in data:
        expense.store_name = str(data['store_name']).strip()
    if 'location_lat' in data:
        expense.location_lat = data['location_lat']
    if 'location_lng' in data:
        expense.location_lng = data['location_lng']
    if 'is_recurring' in data:
        expense.is_recurring = bool(data['is_recurring'])

    expense.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'message': 'Expense updated successfully',
        'expense': expense.to_dict(),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/expenses/<id>
# ─────────────────────────────────────────────────────────────────────────────
@expenses_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete an expense owned by the current user."""
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if expense is None:
        return jsonify({'error': 'Expense not found'}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Expense deleted successfully'}), 200
