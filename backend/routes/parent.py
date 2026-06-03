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
