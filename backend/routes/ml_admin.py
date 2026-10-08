"""
ML admin routes – retraining and model management.
POST /api/ml/retrain-category  – retrain the category classifier
"""

import os
import logging

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User

logger = logging.getLogger(__name__)

ml_admin_bp = Blueprint('ml_admin', __name__)


@ml_admin_bp.route('/ml/retrain-category', methods=['POST'])
@jwt_required()
def retrain_category_model():
    """
    Retrain the expense category classifier.
    Admin only: the caller's email must be listed in the ADMIN_EMAILS setting.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    admins = current_app.config.get('ADMIN_EMAILS', [])
    if not user or user.email.lower() not in admins:
        return jsonify({'error': 'Admin access required'}), 403

    try:
        from ml.train_category_model import train_model
        model = train_model()

        # Reload the singleton in the categorizer
        from ml.categorizer import reload_model
        reload_model()

        return jsonify({
            'message': 'Category classifier retrained successfully',
            'model_type': type(model).__name__,
        }), 200

    except Exception as exc:
        logger.error("Retraining failed: %s", exc)
        return jsonify({'error': f'Retraining failed: {str(exc)}'}), 500
