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
from utils.ratelimit import rate_limit
from utils.mailer import send_email
from utils.tokens import make_token, read_token
from flask import current_app

auth_bp = Blueprint('auth', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/register
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
@rate_limit('register', 10, 3600)
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

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

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
@rate_limit('login', 10, 300)
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


# ─────────────────────────────────────────────────────────────────────────────
# Password reset
# ─────────────────────────────────────────────────────────────────────────────
RESET_MAX_AGE = 3600
VERIFY_MAX_AGE = 3 * 86400


@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit('forgot', 5, 3600)
def forgot_password():
    """Always answers 200 so the endpoint cannot be used to discover which emails exist."""
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    out = {'message': 'If that email has an account, a reset link is on its way.'}
    user = User.query.filter_by(email=email).first() if email else None
    if user:
        token = make_token('reset', user.id, user.password_hash)
        link = '%s/reset-password?token=%s' % (current_app.config['FRONTEND_URL'], token)
        send_email(user.email, 'Reset your SaverAI password',
                   'Open this link within one hour to choose a new password:\n%s\n\nIf you did not ask for this, ignore this email.' % link)
        if current_app.config.get('EXPOSE_AUTH_TOKENS'):
            out['dev_token'] = token
    return jsonify(out), 200


@auth_bp.route('/reset-password', methods=['POST'])
@rate_limit('reset', 10, 3600)
def reset_password():
    data = request.get_json(silent=True) or {}
    token, password = data.get('token'), data.get('password')
    if not isinstance(token, str) or not isinstance(password, str):
        return jsonify({'error': 'token and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    payload, err = read_token('reset', token, RESET_MAX_AGE)
    if err:
        return jsonify({'error': 'This reset link has %s. Request a new one.' % ('expired' if err == 'expired' else 'a problem')}), 400
    user = User.query.get(payload['uid'])
    # The token carries the old password hash tail, so it works exactly once.
    if user is None or not user.password_hash.endswith(payload['fp']):
        return jsonify({'error': 'This reset link was already used. Request a new one.'}), 400
    user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.commit()
    return jsonify({'message': 'Password updated. You can sign in now.'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Email verification
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/send-verification', methods=['POST'])
@jwt_required()
@rate_limit('verify-send', 5, 3600)
def send_verification():
    user = User.query.get(int(get_jwt_identity()))
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    if user.email_verified:
        return jsonify({'message': 'Already verified'}), 200
    token = make_token('verify', user.id, user.email)
    link = '%s/verify-email?token=%s' % (current_app.config['FRONTEND_URL'], token)
    send_email(user.email, 'Verify your SaverAI email', 'Confirm your email by opening:\n%s' % link)
    out = {'message': 'Verification email sent.'}
    if current_app.config.get('EXPOSE_AUTH_TOKENS'):
        out['dev_token'] = token
    return jsonify(out), 200


@auth_bp.route('/verify-email', methods=['POST'])
@rate_limit('verify', 20, 3600)
def verify_email():
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    if not isinstance(token, str):
        return jsonify({'error': 'token is required'}), 400
    payload, err = read_token('verify', token, VERIFY_MAX_AGE)
    if err:
        return jsonify({'error': 'This verification link is not valid. Request a new one.'}), 400
    user = User.query.get(payload['uid'])
    if user is None or not user.email.endswith(payload['fp']):
        return jsonify({'error': 'This verification link is not valid. Request a new one.'}), 400
    user.email_verified = True
    db.session.commit()
    return jsonify({'message': 'Email verified.'}), 200
