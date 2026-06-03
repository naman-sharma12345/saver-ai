"""
Custom decorators for role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from models import User


def student_required(fn):
    """Restrict access to users with the 'student' role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        if user.role != 'student':
            return jsonify({'error': 'Student access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


def parent_required(fn):
    """Restrict access to users with the 'parent' role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        if user.role != 'parent':
            return jsonify({'error': 'Parent access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
