"""
Authentication routes – register, login, refresh, me.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
import math
import re

import bcrypt

from app import db
from models import User
from plans import start_trial_end

auth_bp = Blueprint('auth', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/register
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new student or parent account."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON request body is required'}), 400

    # ── Validate required fields ─────────────────────────────────────
    required = ['email', 'password', 'name']
    missing = [f for f in required if f not in data or not data[f]]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    if not all(isinstance(data[f], str) for f in required):
        return jsonify({'error': 'email, password and name must be strings'}), 400

    email = data['email'].strip().lower()
    password = data['password']
    name = data['name'].strip()
    role = str(data.get('role', 'student')).strip().lower()

    if not EMAIL_RE.match(email) or len(email) > 120:
        return jsonify({'error': 'A valid email address is required'}), 400

    if not name or len(name) > 100:
        return jsonify({'error': 'Name must be 1-100 characters'}), 400

    allowance = data.get('monthly_allowance', 0.0)
    if isinstance(allowance, bool) or not isinstance(allowance, (int, float)) \
            or not math.isfinite(allowance) or allowance < 0:
        return jsonify({'error': 'monthly_allowance must be a non-negative number'}), 400

    if role not in ('student', 'parent'):
        return jsonify({'error': "Role must be 'student' or 'parent'"}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # ── Check for existing user ──────────────────────────────────────────
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    # ── Hash password and create user ────────────────────────────────────
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        email=email,
        password_hash=password_hash,
        role=role,
        name=name,
        monthly_allowance=float(allowance),
        trial_ends_at=start_trial_end(),
    )
    db.session.add(user)
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message': 'Registration successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 201


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/login
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json(silent=True)

    if (not isinstance(data, dict) or not data.get('email') or not data.get('password')
            or not isinstance(data['email'], str) or not isinstance(data['password'], str)):
        return jsonify({'error': 'Email and password are required'}), 400

    email = data['email'].strip().lower()
    password = data['password']

    user = User.query.filter_by(email=email).first()
    if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/refresh
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Return a new access token using a valid refresh token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/auth/me
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Return the currently authenticated user's profile."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200
