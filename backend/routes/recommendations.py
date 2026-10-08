"""
Saving recommendations route.
GET /api/recommendations – returns ML-powered saving tips with daily caching.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from plans import has_feature

from ml.recommendation_engine import cache_recommendations_for_user

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """
    Return AI-generated saving recommendations.
    Cached daily in the saving_recommendations table.
    Generates fresh recommendations if none exist for today.
    """
    user_id = int(get_jwt_identity())
    recommendations = cache_recommendations_for_user(user_id)
    user = User.query.get(user_id)
    # Free plan: a taster of one tip so the habit forms; Pro unlocks every tip.
    locked = not has_feature(user, 'all_tips')
    all_count = len(recommendations)

    total_potential_savings = sum(
        r.get('amount_saved', 0) for r in recommendations
    )

    if locked:
        recommendations = recommendations[:1]

    return jsonify({
        'recommendations': recommendations,
        'locked': locked,
        'total': all_count,
        'total_potential_savings': round(total_potential_savings, 2),
    }), 200
