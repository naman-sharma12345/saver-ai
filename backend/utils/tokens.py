"""Signed, expiring, single-purpose tokens (password reset, email verification)."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _ser(purpose):
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='saverai-' + purpose)


def make_token(purpose, user_id, fingerprint=''):
    """`fingerprint` ties the token to state that changes when it is used (e.g. password hash)."""
    return _ser(purpose).dumps({'uid': user_id, 'fp': fingerprint[-12:]})


def read_token(purpose, token, max_age):
    """Return (data, error) where error is None, 'expired' or 'invalid'."""
    try:
        return _ser(purpose).loads(token, max_age=max_age), None
    except SignatureExpired:
        return None, 'expired'
    except BadSignature:
        return None, 'invalid'
