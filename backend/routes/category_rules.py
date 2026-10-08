"""GET /api/category-rules and DELETE /api/category-rules/<id> - the categories you taught SaverAI."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import CategoryRule

rules_bp = Blueprint('category_rules', __name__)


@rules_bp.route('/category-rules', methods=['GET'])
@jwt_required()
def list_rules():
    user_id = int(get_jwt_identity())
    rules = CategoryRule.query.filter_by(user_id=user_id).order_by(CategoryRule.merchant_key).all()
    return jsonify({'rules': [r.to_dict() for r in rules]}), 200


@rules_bp.route('/category-rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_rule(rule_id):
    user_id = int(get_jwt_identity())
    rule = CategoryRule.query.filter_by(id=rule_id, user_id=user_id).first()
    if rule is None:
        return jsonify({'error': 'Rule not found'}), 404
    db.session.delete(rule)
    db.session.commit()
    return jsonify({'message': 'Rule removed'}), 200
