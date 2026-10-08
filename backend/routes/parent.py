"""
Parent routes – linking and viewing student data.
POST /api/parent/link                              – link to a student by email
GET  /api/parent/student/<student_id>/expenses      – view linked student's expenses
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import User, Expense
from utils.decorators import parent_required
from utils.mailer import send_email
from utils.ratelimit import rate_limit
import time
from datetime import datetime
from sqlalchemy import func
from flask import current_app

parent_bp = Blueprint('parent', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/parent/link
# ─────────────────────────────────────────────────────────────────────────────
@parent_bp.route('/parent/link', methods=['POST'])
@jwt_required()
@parent_required
def link_student():
    """
    Link a student to the authenticated parent by student email.
    Body: { "student_email": "..." }
    """
    parent_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('student_email'):
        return jsonify({'error': 'student_email is required'}), 400

    student_email = data['student_email'].strip().lower()
    student = User.query.filter_by(email=student_email, role='student').first()

    if student is None:
        return jsonify({'error': 'Student not found with that email'}), 404

    if student.parent_id is not None and student.parent_id != parent_id:
        return jsonify({'error': 'Student is already linked to another parent'}), 409

    if student.parent_id == parent_id:
        return jsonify({'message': 'Student is already linked to you', 'student': student.to_dict()}), 200

    student.parent_id = parent_id
    db.session.commit()

    return jsonify({
        'message': 'Student linked successfully',
        'student': student.to_dict(),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/parent/student/<student_id>/expenses
# ─────────────────────────────────────────────────────────────────────────────
@parent_bp.route('/parent/student/<int:student_id>/expenses', methods=['GET'])
@jwt_required()
@parent_required
def get_student_expenses(student_id):
    """Return expenses of a linked student. Parent must be the linked parent."""
    parent_id = int(get_jwt_identity())
    student = User.query.filter_by(id=student_id, role='student').first()

    if student is None:
        return jsonify({'error': 'Student not found'}), 404

    if student.parent_id != parent_id:
        return jsonify({'error': 'You are not linked to this student'}), 403

    # Optional filters
    category = request.args.get('category')
    month = request.args.get('month')

    query = Expense.query.filter_by(user_id=student_id)

    if category:
        query = query.filter(Expense.category.ilike(category))

    if month:
        try:
            from datetime import datetime, timezone
            year, mon = month.split('-')
            start = datetime(int(year), int(mon), 1, tzinfo=timezone.utc)
            if int(mon) == 12:
                end = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(int(year), int(mon) + 1, 1, tzinfo=timezone.utc)
            query = query.filter(Expense.created_at >= start, Expense.created_at < end)
        except (ValueError, IndexError):
            return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

    expenses = query.order_by(Expense.created_at.desc()).all()

    return jsonify({
        'student': student.to_dict(),
        'expenses': [e.to_dict() for e in expenses],
        'total': len(expenses),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/parent/children/<student_id>/remind
# ─────────────────────────────────────────────────────────────────────────────
REMIND_COOLDOWN_SECONDS = 6 * 3600
_last_reminder = {}


@parent_bp.route('/parent/children/<int:student_id>/remind', methods=['POST'])
@jwt_required()
@parent_required
@rate_limit('remind', 20, 3600)
def remind_student(student_id):
    """Email the linked student a friendly allowance check-in. Body: { "note": "optional, 140 chars" }."""
    parent_id = int(get_jwt_identity())
    student = User.query.filter_by(id=student_id, role='student').first()
    if student is None:
        return jsonify({'error': 'Student not found'}), 404
    if student.parent_id != parent_id:
        return jsonify({'error': 'You are not linked to this student'}), 403
    if student.consent_status != 'granted':
        return jsonify({'error': 'This student account is not active yet'}), 409

    note = (request.get_json(silent=True) or {}).get('note') or ''
    if not isinstance(note, str) or len(note) > 140:
        return jsonify({'error': 'note must be text up to 140 characters'}), 400
    note = note.strip()

    key = (parent_id, student_id)
    now = time.monotonic()
    wait = REMIND_COOLDOWN_SECONDS - (now - _last_reminder.get(key, -1e12))
    if wait > 0 and current_app.config.get('RATELIMIT_ENABLED', True):
        return jsonify({'error': 'You already sent a reminder recently. Try again later.', 'retry_after': int(wait)}), 429

    parent = User.query.get(parent_id)
    first = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == student.id, Expense.created_at >= first).scalar() or 0.0
    body = ('Hi %s,\n\n%s sent you a quick check-in on your SaverAI allowance.\n'
            'This month you have logged Rs %s of your Rs %s allowance.\n' % (
                student.name, parent.name, format(round(spent), ','), format(round(student.monthly_allowance or 0), ',')))
    if note:
        body += '\nTheir note: "%s"\n' % note
    body += '\nOpen SaverAI to see how many days your money lasts.'
    send_email(student.email, '%s sent you an allowance check-in' % parent.name, body)
    _last_reminder[key] = now
    return jsonify({'message': 'Reminder sent to %s.' % student.name}), 200
