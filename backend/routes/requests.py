"""Extra-money requests between a student and their linked parent.

POST /api/requests                      student asks for an amount with a short reason
GET  /api/requests                      student: their own; parent: requests addressed to them
POST /api/requests/<id>/decision        parent: {"decision": "approve"|"decline", "note": "optional"}

A request is a record and a nudge, not a payment. SaverAI does not move money.
"""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import AllowanceRequest, User
from utils.mailer import send_email
from utils.ratelimit import rate_limit

requests_bp = Blueprint('allowance_requests', __name__)

MAX_AMOUNT = 100000


@requests_bp.route('/requests', methods=['POST'])
@jwt_required()
@rate_limit('allowance-request', 10, 3600)
def create_request():
    user = User.query.get(int(get_jwt_identity()))
    if user is None or user.role != 'student':
        return jsonify({'error': 'Only students can ask for extra money'}), 403
    if not user.parent_id:
        return jsonify({'error': 'Link a parent in your profile first'}), 400
    parent = User.query.get(user.parent_id)
    if parent is None:
        return jsonify({'error': 'Link a parent in your profile first'}), 400
    data = request.get_json(silent=True) or {}
    amount = data.get('amount')
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not (0 < amount <= MAX_AMOUNT):
        return jsonify({'error': 'amount must be a number above 0 and up to 1,00,000'}), 400
    reason = data.get('reason')
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 140:
        return jsonify({'error': 'Give a short reason (up to 140 characters)'}), 400
    if AllowanceRequest.query.filter_by(student_id=user.id, status='pending').count() >= 1:
        return jsonify({'error': 'You already have a request waiting for your parent'}), 409
    req = AllowanceRequest(student_id=user.id, parent_id=parent.id, amount=round(float(amount), 2), reason=reason.strip())
    db.session.add(req)
    db.session.commit()
    send_email(parent.email, f'{user.name} asked for Rs {req.amount:,.0f}',
               f'{user.name} asked for Rs {req.amount:,.0f} on SaverAI.\n\nReason: {req.reason}\n\n'
               'Open SaverAI to approve or decline. SaverAI does not move money; this is a request and a record.')
    return jsonify(req.to_dict(user.name)), 201


@requests_bp.route('/requests', methods=['GET'])
@jwt_required()
def list_requests():
    user = User.query.get(int(get_jwt_identity()))
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    if user.role == 'parent':
        rows = AllowanceRequest.query.filter_by(parent_id=user.id).order_by(AllowanceRequest.created_at.desc()).limit(50).all()
        names = {u.id: u.name for u in User.query.filter(User.id.in_({r.student_id for r in rows})).all()} if rows else {}
        out = [r.to_dict(names.get(r.student_id)) for r in rows]
    else:
        rows = AllowanceRequest.query.filter_by(student_id=user.id).order_by(AllowanceRequest.created_at.desc()).limit(50).all()
        out = [r.to_dict(user.name) for r in rows]
    return jsonify({'requests': out, 'pending': sum(1 for r in rows if r.status == 'pending')}), 200


@requests_bp.route('/requests/<int:req_id>/decision', methods=['POST'])
@jwt_required()
def decide_request(req_id):
    user = User.query.get(int(get_jwt_identity()))
    if user is None or user.role != 'parent':
        return jsonify({'error': 'Parent access required'}), 403
    req = AllowanceRequest.query.get(req_id)
    if req is None or req.parent_id != user.id:
        return jsonify({'error': 'Request not found'}), 404
    if req.status != 'pending':
        return jsonify({'error': 'That request was already answered'}), 409
    data = request.get_json(silent=True) or {}
    decision = data.get('decision')
    if decision not in ('approve', 'decline'):
        return jsonify({'error': 'decision must be approve or decline'}), 400
    note = data.get('note') or ''
    if not isinstance(note, str) or len(note) > 140:
        return jsonify({'error': 'note must be text up to 140 characters'}), 400
    req.status = 'approved' if decision == 'approve' else 'declined'
    req.parent_note = note.strip() or None
    req.decided_at = datetime.now(timezone.utc)
    db.session.commit()
    student = User.query.get(req.student_id)
    if student is not None:
        send_email(student.email, f'Your request for Rs {req.amount:,.0f} was {req.status}',
                   f'Your parent {req.status} your request for Rs {req.amount:,.0f}.' + (f'\n\nNote: {req.parent_note}' if req.parent_note else ''))
    return jsonify(req.to_dict(student.name if student else None)), 200
