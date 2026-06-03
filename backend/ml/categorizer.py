"""
Expense category predictor – singleton pattern with lazy model loading.

Usage:
    from ml.categorizer import predict_category
    result = predict_category("zomato order biryani")
    # {"category": "Food", "confidence": 0.92}
"""

import os
import logging
import threading
import joblib

logger = logging.getLogger(__name__)

_MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
_PKL_PATH = os.path.join(_MODEL_DIR, 'category_classifier.pkl')
# Fallback to legacy .joblib if .pkl not found
_JOBLIB_PATH = os.path.join(_MODEL_DIR, 'category_classifier.joblib')

_lock = threading.Lock()
_pipeline = None
_loaded = False

# ── Keyword fallback (same as utils/categorizer.py) ─────────────────────────
_KEYWORD_MAP = {
    'Food': [
        'food', 'restaurant', 'cafe', 'pizza', 'burger', 'biryani', 'meal',
        'lunch', 'dinner', 'breakfast', 'snack', 'coffee', 'tea', 'juice',
        'sweets', 'bakery', 'dhaba', 'canteen', 'mess', 'tiffin', 'zomato',
        'swiggy', 'dominos', 'mcdonalds', 'subway', 'starbucks', 'chaiwala',
        'momos', 'samosa', 'chaat', 'thali', 'dosa', 'idli', 'paratha',
        'noodles', 'ice cream', 'cake', 'brownie', 'sandwich', 'maggi',
        'paneer', 'chicken', 'mutton', 'fish', 'kebab', 'shawarma', 'roll',
    ],
    'Transport': [
        'uber', 'ola', 'auto', 'rickshaw', 'metro', 'bus', 'cab', 'taxi',
        'petrol', 'fuel', 'diesel', 'parking', 'toll', 'rapido', 'train',
        'flight', 'ticket', 'travel', 'ride', 'fare', 'shuttle',
    ],
    'Study Materials': [
        'book', 'notebook', 'pen', 'pencil', 'stationery', 'xerox', 'print',
        'photocopy', 'course', 'udemy', 'coursera', 'tuition', 'coaching',
        'library', 'notes', 'textbook', 'study', 'assignment', 'lab',
        'arduino', 'raspberry', 'coding', 'certification',
    ],
    'Entertainment': [
        'movie', 'netflix', 'spotify', 'game', 'gaming', 'concert', 'show',
        'theatre', 'pvr', 'inox', 'party', 'club', 'outing', 'picnic',
        'amazon prime', 'hotstar', 'disney', 'youtube premium', 'bowling',
        'amusement', 'karaoke', 'comedy', 'cricket', 'ipl',
    ],
    'Shopping': [
        'amazon', 'flipkart', 'myntra', 'clothes', 'shoes', 'shirt', 'jeans',
        'jacket', 'watch', 'bag', 'accessory', 'electronics', 'gadget',
        'phone', 'laptop', 'headphones', 'earbuds', 'hoodie', 'perfume',
        'grooming', 'trimmer', 'sunglasses',
    ],
    'Bills': [
        'electricity', 'water', 'internet', 'wifi', 'recharge', 'mobile',
        'phone bill', 'rent', 'maintenance', 'subscription', 'insurance',
        'emi', 'loan', 'broadband', 'dth', 'gas', 'cylinder',
    ],
    'Health': [
        'medicine', 'doctor', 'hospital', 'pharmacy', 'medical', 'gym',
        'fitness', 'health', 'clinic', 'dental', 'eye', 'checkup',
        'apollo', 'prescription', 'protein', 'vitamin', 'supplement',
        'physiotherapy', 'yoga', 'therapy', 'vaccination',
    ],
}


def _keyword_fallback(text: str) -> str:
    """Simple keyword-based categorisation."""
    text_lower = text.lower()
    for category, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return 'Other'


def _load_model():
    """Thread-safe lazy loading of the sklearn pipeline."""
    global _pipeline, _loaded
    if _loaded:
        return

    with _lock:
        if _loaded:
            return
        try:
            path = _PKL_PATH if os.path.exists(_PKL_PATH) else _JOBLIB_PATH
            if os.path.exists(path):
                _pipeline = joblib.load(path)
                logger.info("Category classifier loaded from %s", path)
            else:
                logger.warning("No category classifier model found at %s", _MODEL_DIR)
        except Exception as exc:
            logger.error("Failed to load category classifier: %s", exc)
        finally:
            _loaded = True


def reload_model():
    """Force-reload the model (e.g. after retraining)."""
    global _pipeline, _loaded
    with _lock:
        _pipeline = None
        _loaded = False
    _load_model()


def predict_category(description: str, store_name: str = '') -> dict:
    """
    Predict expense category with confidence score.

    Returns:
        {"category": str, "confidence": float, "method": "ml"|"keyword"|"default"}
    """
    combined = f"{description} {store_name}".strip()
    if not combined:
        return {'category': 'Other', 'confidence': 0.0, 'method': 'default'}

    _load_model()

    # Try ML model
    if _pipeline is not None:
        try:
            prediction = _pipeline.predict([combined])[0]
            probas = _pipeline.predict_proba([combined])[0]
            confidence = float(max(probas))

            if confidence >= 0.5:
                return {
                    'category': prediction,
                    'confidence': round(confidence, 4),
                    'method': 'ml',
                }
            else:
                # Low confidence → try keywords
                kw_cat = _keyword_fallback(combined)
                if kw_cat != 'Other':
                    return {
                        'category': kw_cat,
                        'confidence': round(confidence, 4),
                        'method': 'keyword',
                    }
                return {
                    'category': prediction,
                    'confidence': round(confidence, 4),
                    'method': 'ml_low_confidence',
                }
        except Exception as exc:
            logger.error("ML prediction error: %s", exc)

    # Keyword fallback
    kw_cat = _keyword_fallback(combined)
    return {
        'category': kw_cat,
        'confidence': 0.0,
        'method': 'keyword',
    }
