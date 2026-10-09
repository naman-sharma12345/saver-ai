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
from datetime import date, datetime

import bcrypt

from app import db
from models import User, Expense, Budget, Goal, CategoryRule, AllowanceRequest
from plans import start_trial_end
from utils.ratelimit import rate_limit
from utils.mailer import send_email
from utils.tokens import make_token, read_token
from flask import current_app

auth_bp = Blueprint('auth', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
GUARDIAN_MAX_AGE = 7 * 24 * 3600
ADULT_AGE = 18
MIN_AGE = 8


def _age(dob, today=None):
    today = today or date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _send_guardian_request(user):
    token = make_token('guardian', user.id, user.guardian_email)
    link = '%s/guardian-consent?token=%s' % (current_app.config['FRONTEND_URL'], token)
    send_email(user.guardian_email, 'Approve %s using SaverAI' % user.name,
               '%s signed up for SaverAI, a money tracker for students, and is under 18. '
               'Indian law (DPDP Act) needs a parent or guardian to approve before we handle their data.\n\n'
               'Review and approve or decline here (valid 7 days):\n%s\n\n'
               'We do not show ads or track children for marketing. If you decline, the account and its data are deleted.'
               % (user.name, link))
    return token


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

    if data.get('accept_terms') is not True:
        return jsonify({'error': 'Please accept the Terms and Privacy Policy to continue'}), 400

    dob = None
    guardian_email = None
    if role == 'student':
        try:
            dob = date.fromisoformat(str(data.get('date_of_birth', ''))[:10])
        except ValueError:
            return jsonify({'error': 'date_of_birth is required (YYYY-MM-DD)'}), 400
        age = _age(dob)
        if dob > date.today() or age < MIN_AGE or age > 100:
            return jsonify({'error': 'Please enter a valid date of birth (SaverAI is for ages %d and up)' % MIN_AGE}), 400
        if age < ADULT_AGE:
            guardian_email = str(data.get('guardian_email') or '').strip().lower()
            if not EMAIL_RE.match(guardian_email) or len(guardian_email) > 120:
                return jsonify({'error': 'A parent or guardian email is required for users under 18'}), 400
            if guardian_email == email:
                return jsonify({'error': 'The guardian email must be different from your own'}), 400

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
        date_of_birth=dob,
        guardian_email=guardian_email,
        terms_accepted_at=datetime.utcnow(),
        consent_status='pending' if guardian_email else 'granted',
        consent_at=None if guardian_email else datetime.utcnow(),
    )
    db.session.add(user)
    db.session.commit()

    if guardian_email:
        token = _send_guardian_request(user)
        out = {'message': 'Almost there. We emailed your parent or guardian to approve your account.',
               'consent_required': True}
        if current_app.config.get('EXPOSE_AUTH_TOKENS'):
            out['dev_token'] = token
        return jsonify(out), 202

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

    if user.consent_status == 'pending':
        return jsonify({'error': 'Your parent or guardian has not approved this account yet.',
                        'code': 'consent_pending'}), 403

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


# ─────────────────────────────────────────────────────────────────────────────
# Guardian consent (DPDP Act: verifiable parental consent for under-18s)
# ─────────────────────────────────────────────────────────────────────────────
def _guardian_user(token):
    payload, err = read_token('guardian', token, GUARDIAN_MAX_AGE)
    if err:
        return None
    user = User.query.get(payload['uid'])
    if user is None or user.consent_status != 'pending' or not user.guardian_email \
            or not user.guardian_email.endswith(payload['fp']):
        return None
    return user


@auth_bp.route('/guardian-consent', methods=['GET'])
@rate_limit('guardian-view', 30, 3600)
def guardian_consent_info():
    """Let the guardian see who they are approving before they decide."""
    user = _guardian_user(request.args.get('token', ''))
    if user is None:
        return jsonify({'error': 'This approval link is not valid or has expired.'}), 400
    return jsonify({'name': user.name}), 200


@auth_bp.route('/guardian-consent', methods=['POST'])
@rate_limit('guardian', 20, 3600)
def guardian_consent():
    data = request.get_json(silent=True) or {}
    user = _guardian_user(data.get('token') if isinstance(data.get('token'), str) else '')
    if user is None or not isinstance(data.get('approve'), bool):
        return jsonify({'error': 'This approval link is not valid or has expired.'}), 400
    if not data['approve']:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Declined. The account and its data were deleted.'}), 200
    user.consent_status = 'granted'
    user.consent_at = datetime.utcnow()
    parent = User.query.filter_by(email=user.guardian_email, role='parent').first()
    if parent and not user.parent_id:
        user.parent_id = parent.id
    db.session.commit()
    return jsonify({'message': 'Approved. They can sign in now.'}), 200


@auth_bp.route('/resend-guardian-consent', methods=['POST'])
@rate_limit('guardian-resend', 5, 3600)
def resend_guardian_consent():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email') or '').strip().lower()
    user = User.query.filter_by(email=email).first() if email else None
    out = {'message': 'If that account is waiting for approval, we sent the request again.'}
    if user and user.consent_status == 'pending' and user.guardian_email:
        token = _send_guardian_request(user)
        if current_app.config.get('EXPOSE_AUTH_TOKENS'):
            out['dev_token'] = token
    return jsonify(out), 200


# ─────────────────────────────────────────────────────────────────────────────
# Your data: export and delete (DPDP rights of access and erasure)
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'exported_at': datetime.utcnow().isoformat(),
        'profile': {k: v for k, v in user.to_dict().items() if k != 'entitlement'},
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'guardian_email': user.guardian_email,
        'consent_status': user.consent_status,
        'expenses': [e.to_dict() for e in Expense.query.filter_by(user_id=uid).all()],
        'budgets': [b.to_dict() for b in Budget.query.filter_by(user_id=uid).all()],
        'goals': [{'name': g.name, 'target_amount': g.target_amount, 'saved_amount': g.saved_amount,
                   'deadline': g.deadline.isoformat() if g.deadline else None}
                  for g in Goal.query.filter_by(user_id=uid).all()],
        'category_rules': [r.to_dict() for r in CategoryRule.query.filter_by(user_id=uid).all()],
        'allowance_requests': [r.to_dict() for r in AllowanceRequest.query.filter((AllowanceRequest.student_id == uid) | (AllowanceRequest.parent_id == uid)).all()],
    }), 200


@auth_bp.route('/me', methods=['DELETE'])
@jwt_required()
@rate_limit('delete-account', 5, 3600)
def delete_account():
    """Permanently delete the account and everything attached to it."""
    user = User.query.get(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    password = data.get('password')
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    if not isinstance(password, str) or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Password is incorrect'}), 403
    Goal.query.filter_by(user_id=user.id).delete()
    CategoryRule.query.filter_by(user_id=user.id).delete()
    AllowanceRequest.query.filter((AllowanceRequest.student_id == user.id) | (AllowanceRequest.parent_id == user.id)).delete(synchronize_session=False)
    User.query.filter_by(parent_id=user.id).update({'parent_id': None})
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Your account and data were deleted.'}), 200
