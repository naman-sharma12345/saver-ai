"""
Application factory for the Student Expense Manager Flask backend.
"""

import os
import atexit
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# ─── Extensions (importable from other modules) ─────────────────────────────
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name=None):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    from config import config_by_name
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))

    # Fail fast: never run production with the insecure development secret
    from config import DEV_SECRET
    if config_name == 'production' and app.config.get('JWT_SECRET_KEY') == DEV_SECRET:
        raise RuntimeError('JWT_SECRET_KEY must be set in the environment when FLASK_ENV=production.')

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

    # ── Import models so Alembic / migrate can detect them ───────────────
    with app.app_context():
        from models import User, Expense, Category, Budget, SavingRecommendation, Store  # noqa: F401

    # ── Check for ML models at startup ───────────────────────────────────
    ml_model_dir = app.config.get('ML_MODEL_PATH', os.path.join(os.path.dirname(__file__), 'ml', 'models'))
    pkl_model = os.path.join(ml_model_dir, 'category_classifier.pkl')
    joblib_model = os.path.join(ml_model_dir, 'category_classifier.joblib')

    if not os.path.exists(pkl_model) and not os.path.exists(joblib_model):
        app.logger.warning(
            "⚠️  ML category classifier model not found. "
            "Auto-categorisation will fall back to keywords. "
            "Run `python ml/train_category_model.py` to train the model."
        )
    else:
        app.logger.info("✅ ML category classifier model found.")

    # ── Register blueprints ──────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.expenses import expenses_bp
    from routes.categories import categories_bp
    from routes.budgets import budgets_bp
    from routes.analytics import analytics_bp
    from routes.stores import stores_bp
    from routes.recommendations import recommendations_bp
    from routes.parent import parent_bp
    from routes.ml_admin import ml_admin_bp
    from routes.billing import billing_bp
    from routes.subscriptions import subscriptions_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(expenses_bp, url_prefix='/api')
    app.register_blueprint(categories_bp, url_prefix='/api')
    app.register_blueprint(budgets_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(stores_bp, url_prefix='/api')
    app.register_blueprint(recommendations_bp, url_prefix='/api')
    app.register_blueprint(parent_bp, url_prefix='/api')
    app.register_blueprint(ml_admin_bp, url_prefix='/api')
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    app.register_blueprint(subscriptions_bp, url_prefix='/api')

    # ── APScheduler – daily recommendation generation ────────────────────
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()

        def _daily_recommendations():
            """Generate recommendations for all students at midnight."""
            with app.app_context():
                from ml.recommendation_engine import generate_recommendations, cache_recommendations_for_user
                from models import User as UserModel
                students = UserModel.query.filter_by(role='student').all()
                for student in students:
                    try:
                        cache_recommendations_for_user(student.id)
                    except Exception as exc:
                        app.logger.error("Recs failed for user %d: %s", student.id, exc)
                app.logger.info("Daily recommendation job completed for %d students.", len(students))

        scheduler.add_job(
            func=_daily_recommendations,
            trigger='cron',
            hour=0, minute=0,
            id='daily_recommendations',
            replace_existing=True,
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
        app.logger.info("✅ APScheduler started — daily recommendations at midnight.")
    except ImportError:
        app.logger.warning(
            "⚠️  APScheduler not installed. Daily recommendation job disabled. "
            "Install with: pip install apscheduler"
        )
    except Exception as exc:
        app.logger.warning("⚠️  APScheduler setup failed: %s", exc)

    # ── Health-check endpoint ────────────────────────────────────────────
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'Student Expense Manager API is running'}, 200

    return app
