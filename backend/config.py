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

    # External AI API Key
    AI_API_KEY = os.getenv('AI_API_KEY', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
