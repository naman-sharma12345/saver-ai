"""
Unit tests for ML modules: categorizer, spending predictor,
health score, anomaly detection, and recommendation engine.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Category Classifier Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestCategorizer:
    """Test the expense category predictor."""

    def test_predict_returns_dict(self):
        from ml.categorizer import predict_category
        result = predict_category("lunch at dominos with friends")
        assert isinstance(result, dict)
        assert 'category' in result
        assert 'confidence' in result
        assert 'method' in result

    def test_predict_food_keywords(self):
        from ml.categorizer import predict_category
        result = predict_category("zomato order biryani")
        assert result['category'] == 'Food'

    def test_predict_transport_keywords(self):
        from ml.categorizer import predict_category
        result = predict_category("uber ride to college")
        assert result['category'] == 'Transport'

    def test_predict_study_materials(self):
        from ml.categorizer import predict_category
        result = predict_category("textbook purchase from store")
        assert result['category'] == 'Study Materials'

    def test_predict_entertainment(self):
        from ml.categorizer import predict_category
        result = predict_category("netflix subscription monthly")
        assert result['category'] == 'Entertainment'

    def test_predict_shopping(self):
        from ml.categorizer import predict_category
        result = predict_category("amazon order headphones")
        assert result['category'] == 'Shopping'

    def test_predict_bills(self):
        from ml.categorizer import predict_category
        result = predict_category("electricity bill payment")
        assert result['category'] == 'Bills'

    def test_predict_health(self):
        from ml.categorizer import predict_category
        result = predict_category("medicine from pharmacy")
        assert result['category'] == 'Health'

    def test_empty_input_returns_other(self):
        from ml.categorizer import predict_category
        result = predict_category("")
        assert result['category'] == 'Other'

    def test_store_name_helps(self):
        from ml.categorizer import predict_category
        result = predict_category("quick snack", "Dominos")
        assert result['category'] == 'Food'

    def test_confidence_in_range(self):
        from ml.categorizer import predict_category
        result = predict_category("lunch at canteen")
        assert 0.0 <= result['confidence'] <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Spending Predictor Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestSpendingPredictor:
    """Test the monthly spending prediction module."""

    def test_prediction_returns_dict(self, app):
        with app.app_context():
            from ml.spending_predictor import predict_next_month_spending
            result = predict_next_month_spending(user_id=1)
            assert isinstance(result, dict)
            assert 'predicted_amount' in result
            assert 'confidence_interval' in result
            assert 'method' in result
            assert 'monthly_history' in result

    def test_prediction_non_negative(self, app):
        with app.app_context():
            from ml.spending_predictor import predict_next_month_spending
            result = predict_next_month_spending(user_id=1)
            assert result['predicted_amount'] >= 0

    def test_confidence_interval_valid(self, app):
        with app.app_context():
            from ml.spending_predictor import predict_next_month_spending
            result = predict_next_month_spending(user_id=1)
            ci = result['confidence_interval']
            assert ci['lower'] <= ci['upper']
            assert ci['lower'] >= 0

    def test_nonexistent_user_returns_data(self, app):
        with app.app_context():
            from ml.spending_predictor import predict_next_month_spending
            result = predict_next_month_spending(user_id=99999)
            assert result['method'] in ('insufficient_data', 'global_average')


# ─────────────────────────────────────────────────────────────────────────────
# 3. Financial Health Score Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestHealthScore:
    """Test the financial health score calculator."""

    def test_returns_score_and_breakdown(self, app):
        with app.app_context():
            from ml.health_score import compute_financial_health
            result = compute_financial_health(user_id=1)
            assert 'score' in result
            assert 'breakdown' in result
            assert 0 <= result['score'] <= 100

    def test_breakdown_components(self, app):
        with app.app_context():
            from ml.health_score import compute_financial_health
            result = compute_financial_health(user_id=1)
            bd = result['breakdown']
            assert 'savings' in bd
            assert 'budget' in bd
            assert 'discipline' in bd
            assert bd['savings']['max'] == 40
            assert bd['budget']['max'] == 30
            assert bd['discipline']['max'] == 30

    def test_scores_sum_to_total(self, app):
        with app.app_context():
            from ml.health_score import compute_financial_health
            result = compute_financial_health(user_id=1)
            bd = result['breakdown']
            component_sum = (
                bd['savings']['score'] +
                bd['budget']['score'] +
                bd['discipline']['score']
            )
            assert abs(result['score'] - component_sum) <= 1  # rounding tolerance

    def test_nonexistent_user(self, app):
        with app.app_context():
            from ml.health_score import compute_financial_health
            result = compute_financial_health(user_id=99999)
            assert 'error' in result


# ─────────────────────────────────────────────────────────────────────────────
# 4. Anomaly Detection Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestAnomalyDetection:
    """Test the Isolation Forest anomaly detector."""

    def test_returns_list(self, app):
        with app.app_context():
            from ml.anomaly_detection import detect_anomalies
            result = detect_anomalies(user_id=1)
            assert isinstance(result, list)

    def test_anomaly_has_required_fields(self, app):
        with app.app_context():
            from ml.anomaly_detection import detect_anomalies
            result = detect_anomalies(user_id=1)
            if result:  # might not detect anomalies with small dataset
                a = result[0]
                assert 'expense_id' in a
                assert 'anomaly_score' in a
                assert 'explanation' in a
                assert 'expense' in a

    def test_insufficient_data_returns_empty(self, app):
        with app.app_context():
            from ml.anomaly_detection import detect_anomalies
            result = detect_anomalies(user_id=99999)
            assert result == []

    def test_flag_in_db(self, app):
        with app.app_context():
            from ml.anomaly_detection import flag_anomalies_in_db
            count = flag_anomalies_in_db(user_id=1)
            assert isinstance(count, int)
            assert count >= 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Recommendation Engine Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestRecommendationEngine:
    """Test the recommendation engine."""

    def test_returns_list(self, app):
        with app.app_context():
            from ml.recommendation_engine import generate_recommendations
            result = generate_recommendations(user_id=1)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_recommendation_has_text_and_amount(self, app):
        with app.app_context():
            from ml.recommendation_engine import generate_recommendations
            result = generate_recommendations(user_id=1)
            for rec in result:
                assert 'recommendation_text' in rec
                assert 'amount_saved' in rec

    def test_nonexistent_user_returns_empty(self, app):
        with app.app_context():
            from ml.recommendation_engine import generate_recommendations
            result = generate_recommendations(user_id=99999)
            assert result == []

    def test_cache_function(self, app):
        with app.app_context():
            from ml.recommendation_engine import cache_recommendations_for_user
            result = cache_recommendations_for_user(user_id=1)
            assert isinstance(result, list)
            assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 6. Store Finder Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestStoreFinder:
    """Test the store finder utility."""

    def test_find_cheaper_returns_dict(self, app):
        with app.app_context():
            from utils.store_finder import find_cheaper_alternatives
            result = find_cheaper_alternatives(expense_id=1)
            assert isinstance(result, dict)
            assert 'original' in result
            assert 'alternatives' in result

    def test_nonexistent_expense(self, app):
        with app.app_context():
            from utils.store_finder import find_cheaper_alternatives
            result = find_cheaper_alternatives(expense_id=99999)
            assert 'error' in result


# ─────────────────────────────────────────────────────────────────────────────
# 7. API Endpoint Integration Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestEndpoints:
    """Integration tests for the ML-powered API endpoints."""

    def test_health_check(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'ok'

    def test_create_expense_auto_categorize(self, client, auth_headers):
        resp = client.post('/api/expenses', headers=auth_headers, json={
            'amount': 350,
            'description': 'Pizza from Dominos for dinner',
            'store_name': 'Dominos Pizza',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['expense']['category'] == 'Food'
        assert 'categorization' in data

    def test_anomalies_endpoint(self, client, auth_headers):
        resp = client.get('/api/expenses/anomalies', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'anomalies' in data
        assert 'total' in data

    def test_financial_health_endpoint(self, client, auth_headers):
        resp = client.get('/api/analytics/financial-health-score', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'score' in data
        assert 'breakdown' in data
        assert 0 <= data['score'] <= 100

    def test_next_month_prediction_endpoint(self, client, auth_headers):
        resp = client.get('/api/analytics/next-month-prediction', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'predicted_amount' in data
        assert 'confidence_interval' in data

    def test_recommendations_endpoint(self, client, auth_headers):
        resp = client.get('/api/recommendations', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'recommendations' in data
        assert len(data['recommendations']) > 0

    def test_cheaper_alternatives_endpoint(self, client, auth_headers):
        resp = client.post('/api/stores/cheaper-alternatives', headers=auth_headers, json={
            'expense_id': 1,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'original' in data
        assert 'alternatives' in data

    def test_retrain_requires_parent(self, client, auth_headers):
        resp = client.post('/api/ml/retrain-category', headers=auth_headers)
        assert resp.status_code == 403
