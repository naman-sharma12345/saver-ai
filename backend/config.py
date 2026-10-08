"""
Configuration module for Student Expense Manager.
Loads environment variables and defines application-wide settings.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file from the backend directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


# Insecure default, usable only outside production. ProductionConfig refuses to run with it.
DEV_SECRET = 'dev-only-insecure-secret'


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', DEV_SECRET)

    # Database — defaults to SQLite; swap the env var to PostgreSQL for prod
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        'sqlite:///' + os.path.join(basedir, 'student_expense.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', DEV_SECRET)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # ML Model Path
    ML_MODEL_PATH = os.path.join(basedir, 'ml', 'models')

    # Allowed CORS origins (comma-separated). Defaults to local dev frontends.
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:80').split(',')
        if o.strip()
    ]

    # Emails allowed to use admin endpoints such as model retraining (comma-separated)
    ADMIN_EMAILS = [
        e.strip().lower()
        for e in os.getenv('ADMIN_EMAILS', '').split(',')
        if e.strip()
    ]

    # All "AI" in SaverAI is local machine learning (scikit-learn). No LLM or model API keys.

    # Auth hardening
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', '1') == '1'
    TRUST_PROXY = os.getenv('TRUST_PROXY', '0') == '1'
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    # Email (leave SMTP_HOST empty to only log emails in development)
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = os.getenv('SMTP_PORT', '587')
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    MAIL_FROM = os.getenv('MAIL_FROM', '')
    # Return reset/verify tokens in API responses. Development and tests only.
    EXPOSE_AUTH_TOKENS = False
    # TODO(supabase): when moving auth/db to Supabase, set these and swap routes/auth.py
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')

    # Billing. With no Razorpay keys the app runs in mock mode (no real charges).
    TRIAL_DAYS = int(os.getenv('TRIAL_DAYS', '7'))
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
    RAZORPAY_PLAN_ID_MONTHLY = os.getenv('RAZORPAY_PLAN_ID_MONTHLY', '')
    RAZORPAY_PLAN_ID_YEARLY = os.getenv('RAZORPAY_PLAN_ID_YEARLY', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    EXPOSE_AUTH_TOKENS = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    IS_PRODUCTION = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    EXPOSE_AUTH_TOKENS = True
    RATELIMIT_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
