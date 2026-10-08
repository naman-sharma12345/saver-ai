"""Tiny in-memory sliding-window rate limiter for auth endpoints.

Good enough for a single process. TODO(scale): swap the store for Redis when running
several workers (the function signature stays the same).
"""
import threading
import time
from collections import defaultdict, deque
from functools import wraps

from flask import current_app, jsonify, request

_hits = defaultdict(deque)
_lock = threading.Lock()


def reset():
    with _lock:
        _hits.clear()


def _client_ip():
    # Behind a proxy set TRUST_PROXY=1 so X-Forwarded-For is honoured (first hop only).
    if current_app.config.get('TRUST_PROXY'):
        fwd = request.headers.get('X-Forwarded-For', '')
        if fwd:
            return fwd.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def rate_limit(name, limit, window_seconds):
    """Allow `limit` calls per `window_seconds` per client IP for the named bucket."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_app.config.get('RATELIMIT_ENABLED', True):
                return fn(*args, **kwargs)
            key = (name, _client_ip())
            now = time.monotonic()
            with _lock:
                q = _hits[key]
                while q and now - q[0] > window_seconds:
                    q.popleft()
                if len(q) >= limit:
                    retry = max(1, int(window_seconds - (now - q[0])))
                    resp = jsonify({'error': 'Too many attempts. Please wait and try again.', 'retry_after': retry})
                    resp.status_code = 429
                    resp.headers['Retry-After'] = str(retry)
                    return resp
                q.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return deco
