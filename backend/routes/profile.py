"""
User profile routes – GET / PUT /api/profile.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import User

profile_bp = Blueprint('profile', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/profile
# ─────────────────────────────────────────────────────────────────────────────
@profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Return the authenticated user's profile."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/profile
# ─────────────────────────────────────────────────────────────────────────────
@profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update the authenticated user's name and/or monthly_allowance."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if user is None:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'name' in data and data['name']:
        user.name = data['name'].strip()

    if 'monthly_allowance' in data:
        try:
            user.monthly_allowance = float(data['monthly_allowance'])
        except (ValueError, TypeError):
            return jsonify({'error': 'monthly_allowance must be a number'}), 400

    db.session.commit()

    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict(),
    }), 200
