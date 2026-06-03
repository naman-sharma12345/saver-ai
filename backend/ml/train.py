"""
Train the expense category classifier.

This script will:
1. Load training data (from CSV or database).
2. Train a TF-IDF + classifier pipeline.
3. Save the model artifacts to ml/models/.

Usage:
    python ml/train.py

NOTE: This is a scaffold. A full training pipeline will be implemented in Prompt 2.
"""

import os
import sys
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'category_classifier.joblib')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')


def generate_synthetic_data() -> pd.DataFrame:
    """Generate synthetic training data for category classification."""
    data = [
        # Food
        ('Lunch at canteen', 'Food'), ('Dinner at restaurant', 'Food'),
        ('Dominos pizza order', 'Food'), ('Coffee at Starbucks', 'Food'),
        ('Biryani from Zomato', 'Food'), ('Breakfast sandwich', 'Food'),
        ('Tea and snacks', 'Food'), ('Swiggy food delivery', 'Food'),
        ('McDonalds burger meal', 'Food'), ('Juice from fresh bar', 'Food'),
        ('Mess monthly fee', 'Food'), ('Bakery pastry', 'Food'),
        # Transport
        ('Uber ride to college', 'Transport'), ('Metro card recharge', 'Transport'),
        ('Auto rickshaw fare', 'Transport'), ('Ola cab booking', 'Transport'),
        ('Petrol for bike', 'Transport'), ('Bus ticket', 'Transport'),
        ('Rapido bike taxi', 'Transport'), ('Parking charges', 'Transport'),
        ('Train ticket booking', 'Transport'), ('Toll charges highway', 'Transport'),
        # Study Materials
        ('Textbook purchase', 'Study Materials'), ('Notebook and pens', 'Study Materials'),
        ('Xerox copies notes', 'Study Materials'), ('Udemy course purchase', 'Study Materials'),
        ('Stationery supplies', 'Study Materials'), ('Photocopy of assignment', 'Study Materials'),
        ('Coursera subscription', 'Study Materials'), ('Library fine', 'Study Materials'),
        ('Printing project report', 'Study Materials'), ('Reference book', 'Study Materials'),
        # Entertainment
        ('Netflix subscription', 'Entertainment'), ('Movie tickets PVR', 'Entertainment'),
        ('Spotify premium', 'Entertainment'), ('Gaming credits', 'Entertainment'),
        ('Concert tickets', 'Entertainment'), ('Party expenses', 'Entertainment'),
        ('Amazon Prime subscription', 'Entertainment'), ('Disney Hotstar', 'Entertainment'),
        ('Bowling alley outing', 'Entertainment'), ('Amusement park tickets', 'Entertainment'),
        # Shopping
        ('Amazon order electronics', 'Shopping'), ('Myntra clothes purchase', 'Shopping'),
        ('New shoes Nike', 'Shopping'), ('Flipkart order', 'Shopping'),
        ('Watch purchase', 'Shopping'), ('Bag backpack new', 'Shopping'),
        ('Headphones wireless', 'Shopping'), ('Phone cover case', 'Shopping'),
        ('Clothes shirt jeans', 'Shopping'), ('Laptop accessories', 'Shopping'),
        # Bills
        ('Electricity bill', 'Bills'), ('Mobile recharge', 'Bills'),
        ('Internet wifi bill', 'Bills'), ('Water bill payment', 'Bills'),
        ('Room rent monthly', 'Bills'), ('Insurance premium', 'Bills'),
        ('Subscription renewal', 'Bills'), ('EMI payment loan', 'Bills'),
        ('Maintenance charges', 'Bills'), ('Phone bill postpaid', 'Bills'),
        # Health
        ('Medicine from pharmacy', 'Health'), ('Doctor consultation', 'Health'),
        ('Gym membership', 'Health'), ('Dental checkup', 'Health'),
        ('Apollo pharmacy purchase', 'Health'), ('Eye checkup', 'Health'),
        ('Medical test blood', 'Health'), ('Fitness equipment', 'Health'),
        ('Hospital visit', 'Health'), ('Prescription medicines', 'Health'),
        # Other
        ('Miscellaneous expense', 'Other'), ('Donation charity', 'Other'),
        ('Gift for friend birthday', 'Other'), ('Laundry dry cleaning', 'Other'),
        ('Passport application', 'Other'), ('Courier delivery charges', 'Other'),
    ]
    return pd.DataFrame(data, columns=['description', 'category'])


def train_model():
    """Train and save the category classifier."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    logger.info("Generating synthetic training data...")
    df = generate_synthetic_data()
    logger.info("Dataset size: %d samples, %d categories", len(df), df['category'].nunique())

    X = df['description']
    y = df['category']

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Vectorize
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words='english',
        lowercase=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Train
    model = MultinomialNB(alpha=0.1)
    model.fit(X_train_vec, y_train)

    # Evaluate
    y_pred = model.predict(X_test_vec)
    logger.info("\n%s", classification_report(y_test, y_pred))

    accuracy = model.score(X_test_vec, y_test)
    logger.info("Test accuracy: %.2f%%", accuracy * 100)

    # Save
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    logger.info("Model saved to %s", MODEL_PATH)
    logger.info("Vectorizer saved to %s", VECTORIZER_PATH)

    return model, vectorizer


if __name__ == '__main__':
    train_model()
