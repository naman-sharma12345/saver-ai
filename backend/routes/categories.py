"""
Category routes – GET /api/categories.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from models import Category

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Return all categories (default + custom)."""
    categories = Category.query.order_by(Category.name).all()
    return jsonify({
        'categories': [c.to_dict() for c in categories],
    }), 200
