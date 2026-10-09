"""GET /api/onboarding - first-run checklist derived from what the user has actually done."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Expense, Budget, Goal, User

onboarding_bp = Blueprint('onboarding', __name__)


@onboarding_bp.route('/onboarding', methods=['GET'])
@jwt_required()
def onboarding():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    steps = [
        {'key': 'allowance', 'title': 'Set your monthly allowance', 'done': bool(user and (user.monthly_allowance or 0) > 0), 'path': '/profile'},
        {'key': 'expense', 'title': 'Log your first expense', 'done': Expense.query.filter_by(user_id=uid).count() > 0, 'path': '/expenses'},
        {'key': 'budget', 'title': 'Set a category budget', 'done': Budget.query.filter_by(user_id=uid).count() > 0, 'path': '/budget'},
        {'key': 'goal', 'title': 'Start a savings goal', 'done': Goal.query.filter_by(user_id=uid).count() > 0, 'path': '/goals'},
    ]
    done = sum(1 for s in steps if s['done'])
    return jsonify({'steps': steps, 'done': done, 'total': len(steps), 'complete': done == len(steps)}), 200
