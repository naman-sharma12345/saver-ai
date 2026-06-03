"""
Expense auto-categoriser.
Attempts to load a trained ML model; falls back to keyword heuristics or 'Other'.
"""

import os
import logging
import joblib

logger = logging.getLogger(__name__)

_model = None
_vectorizer = None
_model_loaded = False

# Path where the trained model artifacts are stored
_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml', 'models')
_MODEL_PATH = os.path.join(_MODEL_DIR, 'category_classifier.joblib')
_VECTORIZER_PATH = os.path.join(_MODEL_DIR, 'tfidf_vectorizer.joblib')


def _load_model():
    """Load the ML model once (lazy singleton)."""
    global _model, _vectorizer, _model_loaded
    if _model_loaded:
        return

    try:
        if os.path.exists(_MODEL_PATH) and os.path.exists(_VECTORIZER_PATH):
            _model = joblib.load(_MODEL_PATH)
            _vectorizer = joblib.load(_VECTORIZER_PATH)
            logger.info("ML category classifier loaded successfully.")
        else:
            logger.warning("ML model files not found – using keyword fallback.")
    except Exception as exc:
        logger.error("Failed to load ML model: %s", exc)
    finally:
        _model_loaded = True


# ── Keyword-based fallback ───────────────────────────────────────────────────
KEYWORD_MAP = {
    'Food': [
        'food', 'restaurant', 'cafe', 'pizza', 'burger', 'biryani', 'meal',
        'lunch', 'dinner', 'breakfast', 'snack', 'coffee', 'tea', 'juice',
        'sweets', 'bakery', 'dhaba', 'canteen', 'mess', 'tiffin', 'zomato',
        'swiggy', 'dominos', 'mcdonalds', 'subway', 'starbucks', 'chaiwala',
    ],
    'Transport': [
        'uber', 'ola', 'auto', 'rickshaw', 'metro', 'bus', 'cab', 'taxi',
        'petrol', 'fuel', 'diesel', 'parking', 'toll', 'rapido', 'train',
        'flight', 'ticket', 'travel',
    ],
    'Study Materials': [
        'book', 'notebook', 'pen', 'pencil', 'stationery', 'xerox', 'print',
        'photocopy', 'course', 'udemy', 'coursera', 'tuition', 'coaching',
        'library', 'notes', 'textbook',
    ],
    'Entertainment': [
        'movie', 'netflix', 'spotify', 'game', 'gaming', 'concert', 'show',
        'theatre', 'pvr', 'inox', 'party', 'club', 'outing', 'picnic',
        'amazon prime', 'hotstar', 'disney', 'youtube premium',
    ],
    'Shopping': [
        'amazon', 'flipkart', 'myntra', 'clothes', 'shoes', 'shirt', 'jeans',
        'jacket', 'watch', 'bag', 'accessory', 'electronics', 'gadget',
        'phone', 'laptop', 'headphones', 'earbuds',
    ],
    'Bills': [
        'electricity', 'water', 'internet', 'wifi', 'recharge', 'mobile',
        'phone bill', 'rent', 'maintenance', 'subscription', 'insurance',
        'emi', 'loan',
    ],
    'Health': [
        'medicine', 'doctor', 'hospital', 'pharmacy', 'medical', 'gym',
        'fitness', 'health', 'clinic', 'dental', 'eye', 'checkup',
        'apollo', 'prescription',
    ],
}


def _keyword_categorise(text: str) -> str:
    """Simple keyword lookup categorisation."""
    text_lower = text.lower()
    for category, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return 'Other'


def categorise_expense(description: str, store_name: str = '') -> str:
    """
    Predict the category for an expense.

    1. Try the ML model if loaded.
    2. Fall back to keyword matching.
    3. Default to 'Other'.
    """
    combined_text = f"{description} {store_name}".strip()
    if not combined_text:
        return 'Other'

    _load_model()

    # Attempt ML prediction
    if _model is not None and _vectorizer is not None:
        try:
            features = _vectorizer.transform([combined_text])
            prediction = _model.predict(features)[0]
            return prediction
        except Exception as exc:
            logger.error("ML prediction failed: %s – falling back to keywords.", exc)

    # Keyword fallback
    return _keyword_categorise(combined_text)
