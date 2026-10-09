"""GET /api/streak - logging streak and badges. Free for everyone: the habit is the product."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Expense
from ml.streaks import streak_summary

streak_bp = Blueprint('streak', __name__)


@streak_bp.route('/streak', methods=['GET'])
@jwt_required()
def streak():
    uid = int(get_jwt_identity())
    return jsonify(streak_summary(Expense.query.filter_by(user_id=uid).all())), 200
