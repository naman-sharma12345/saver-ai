"""
Prediction module for the expense category classifier.

Usage:
    from ml.predict import predict_category
    category = predict_category("Lunch at dominos with friends")
"""

import os
import logging
import joblib

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'category_classifier.joblib')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')

_model = None
_vectorizer = None


def _load():
    """Lazy-load model and vectorizer."""
    global _model, _vectorizer
    if _model is not None:
        return True
    try:
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            _model = joblib.load(MODEL_PATH)
            _vectorizer = joblib.load(VECTORIZER_PATH)
            logger.info("ML model loaded from %s", MODEL_PATH)
            return True
        else:
            logger.warning("Model files not found at %s", MODEL_DIR)
            return False
    except Exception as exc:
        logger.error("Failed to load ML model: %s", exc)
        return False


def predict_category(text: str) -> str | None:
    """
    Predict the expense category for the given text.
    Returns the category string or None if the model is unavailable.
    """
    if not _load():
        return None

    try:
        features = _vectorizer.transform([text])
        prediction = _model.predict(features)[0]
        return prediction
    except Exception as exc:
        logger.error("Prediction failed: %s", exc)
        return None


def predict_with_confidence(text: str) -> tuple[str | None, float]:
    """
    Predict category with confidence score.
    Returns (category, confidence) or (None, 0.0).
    """
    if not _load():
        return None, 0.0

    try:
        features = _vectorizer.transform([text])
        prediction = _model.predict(features)[0]
        probabilities = _model.predict_proba(features)[0]
        confidence = max(probabilities)
        return prediction, round(confidence, 4)
    except Exception as exc:
        logger.error("Prediction failed: %s", exc)
        return None, 0.0
