"""
Store comparison routes.
GET  /api/stores/nearby?lat=..&lng=..&radius=5&category=Food
POST /api/stores/cheaper-alternatives  – find cheaper store alternatives for an expense
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from geopy.distance import geodesic

from models import Store, Expense
from utils.store_finder import find_cheaper_alternatives

stores_bp = Blueprint('stores', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/stores/nearby
# ─────────────────────────────────────────────────────────────────────────────
@stores_bp.route('/stores/nearby', methods=['GET'])
@jwt_required()
def nearby_stores():
    """
    Find nearby stores sorted by distance and average_price_level.
    Query params:
        lat       – latitude  (required)
        lng       – longitude (required)
        radius    – search radius in km (default 5)
        category  – filter by store category (optional)
    """
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 5.0, type=float)
    category = request.args.get('category')

    if lat is None or lng is None:
        return jsonify({'error': 'lat and lng query parameters are required'}), 400

    user_location = (lat, lng)

    query = Store.query
    if category:
        query = query.filter(Store.category.ilike(f'%{category}%'))

    stores = query.all()

    # Calculate distance for each store and filter by radius
    results = []
    for store in stores:
        store_location = (store.lat, store.lng)
        try:
            distance_km = geodesic(user_location, store_location).km
        except Exception:
            continue

        if distance_km <= radius:
            store_dict = store.to_dict()
            store_dict['distance_km'] = round(distance_km, 2)
            results.append(store_dict)

    # Sort by distance first, then by price level
    results.sort(key=lambda s: (s['distance_km'], s['average_price_level']))

    # Identify cheapest option
    cheapest = None
    if results:
        cheapest = min(results, key=lambda s: s['average_price_level'])

    return jsonify({
        'stores': results,
        'total': len(results),
        'cheapest': cheapest,
        'search_params': {
            'lat': lat,
            'lng': lng,
            'radius_km': radius,
            'category': category,
        },
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/stores/cheaper-alternatives
# ─────────────────────────────────────────────────────────────────────────────
@stores_bp.route('/stores/cheaper-alternatives', methods=['POST'])
@jwt_required()
def cheaper_alternatives():
    """
    Find cheaper store alternatives for a given expense.
    Body: { "expense_id": int, "radius_km": float (optional, default 5) }

    Returns:
        - The original store and price
        - Up to 3 alternate stores with lower price levels
        - Estimated saving per store
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or 'expense_id' not in data:
        return jsonify({'error': 'expense_id is required'}), 400

    expense_id = int(data['expense_id'])
    radius_km = float(data.get('radius_km', 5.0))

    # Verify ownership
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if not expense:
        return jsonify({'error': 'Expense not found or not yours'}), 404

    result = find_cheaper_alternatives(expense_id, radius_km)

    if 'error' in result:
        return jsonify(result), 404

    return jsonify(result), 200
