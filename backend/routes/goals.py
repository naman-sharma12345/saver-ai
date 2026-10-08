"""Savings goals. Free for everyone: a goal is the reason students keep opening the app.

GET    /api/goals                    list goals with projections
POST   /api/goals                    create
PUT    /api/goals/<id>               update name, target, deadline
DELETE /api/goals/<id>               delete
POST   /api/goals/<id>/contribute    add (or with a negative amount, take out) savings
"""
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from models import db, Expense, Goal, User
from ml.goal_planner import project_goal

goals_bp = Blueprint('goals', __name__)

MAX_GOALS = 20
MAX_AMOUNT = 10_000_000


def _surplus(user_id):
    """Rough monthly surplus: allowance minus the last 30 days of spending."""
    user = User.query.get(user_id)
    if not user or not user.monthly_allowance:
        return None
    since = datetime.utcnow() - timedelta(days=30)
    spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == user_id, Expense.created_at >= since).scalar() or 0.0
    return user.monthly_allowance - spent


def _out(goal, surplus):
    d = {
        'id': goal.id, 'name': goal.name, 'target_amount': goal.target_amount,
        'saved_amount': goal.saved_amount,
        'deadline': goal.deadline.isoformat() if goal.deadline else None,
    }
    d.update(project_goal(goal, monthly_surplus=surplus))
    return d


def _num(value, field, allow_zero=False):
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field} must be a number')
    if n != n or n in (float('inf'), float('-inf')) or abs(n) > MAX_AMOUNT:
        raise ValueError(f'{field} is out of range')
    if n < 0 or (n == 0 and not allow_zero):
        raise ValueError(f'{field} must be greater than zero')
    return n


def _date(value):
    if value in (None, ''):
        return None
    try:
        d = date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ValueError('deadline must be YYYY-MM-DD')
    if d < date.today():
        raise ValueError('deadline must be in the future')
    return d


def _name(value):
    name = (value or '').strip() if isinstance(value, str) else ''
    if not name or len(name) > 80:
        raise ValueError('name is required (max 80 characters)')
    return name


def _mine(goal_id):
    return Goal.query.filter_by(id=goal_id, user_id=int(get_jwt_identity())).first()


@goals_bp.route('/goals', methods=['GET'])
@jwt_required()
def list_goals():
    uid = int(get_jwt_identity())
    surplus = _surplus(uid)
    goals = Goal.query.filter_by(user_id=uid).order_by(Goal.id.desc()).all()
    return jsonify({'goals': [_out(g, surplus) for g in goals]}), 200


@goals_bp.route('/goals', methods=['POST'])
@jwt_required()
def create_goal():
    uid = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    if Goal.query.filter_by(user_id=uid).count() >= MAX_GOALS:
        return jsonify({'error': f'You can keep up to {MAX_GOALS} goals'}), 400
    try:
        goal = Goal(user_id=uid, name=_name(data.get('name')), target_amount=_num(data.get('target_amount'), 'target_amount'),
                    saved_amount=_num(data.get('saved_amount', 0), 'saved_amount', allow_zero=True),
                    deadline=_date(data.get('deadline')))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    db.session.add(goal)
    db.session.commit()
    return jsonify(_out(goal, _surplus(uid))), 201


@goals_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    goal = _mine(goal_id)
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
    data = request.get_json(silent=True) or {}
    try:
        if 'name' in data:
            goal.name = _name(data['name'])
        if 'target_amount' in data:
            goal.target_amount = _num(data['target_amount'], 'target_amount')
        if 'deadline' in data:
            goal.deadline = _date(data['deadline'])
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    db.session.commit()
    return jsonify(_out(goal, _surplus(goal.user_id))), 200


@goals_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    goal = _mine(goal_id)
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Goal deleted'}), 200


@goals_bp.route('/goals/<int:goal_id>/contribute', methods=['POST'])
@jwt_required()
def contribute(goal_id):
    goal = _mine(goal_id)
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get('amount'))
        if amount != amount or abs(amount) > MAX_AMOUNT or amount == 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'amount must be a non-zero number'}), 400
    goal.saved_amount = max(0.0, round((goal.saved_amount or 0) + amount, 2))
    db.session.commit()
    return jsonify(_out(goal, _surplus(goal.user_id))), 200
