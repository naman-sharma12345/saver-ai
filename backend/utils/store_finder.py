"""
Store finder utility.

Provides helper functions for finding cheaper store alternatives
for a given expense.

Usage (within Flask app context):
    from utils.store_finder import find_cheaper_alternatives
    result = find_cheaper_alternatives(expense_id=5)
"""

import logging
from geopy.distance import geodesic

from models import Expense, Store

logger = logging.getLogger(__name__)

# Price level difference → estimated percentage saving
# Level 1 diff ≈ 7.5%, Level 2 diff ≈ 15%, Level 3 diff ≈ 22.5%
SAVINGS_PER_LEVEL = 7.5


def find_cheaper_alternatives(expense_id: int, radius_km: float = 5.0) -> dict:
    """
    Given an expense ID, find up to 3 cheaper store alternatives
    within the specified radius selling the same category of goods.

    Returns:
        {
            "original": {expense details + store info},
            "alternatives": [
                {store details, distance_km, estimated_saving, savings_pct},
                ...
            ],
            "total_potential_saving": float,
        }
    """
    expense = Expense.query.get(expense_id)
    if not expense:
        return {'error': 'Expense not found'}

    # Determine reference location (expense location or default Noida Sec-62)
    ref_lat = expense.location_lat or 28.6270
    ref_lng = expense.location_lng or 77.3650
    ref_location = (ref_lat, ref_lng)

    # Find the original store's price level
    original_store = None
    original_price_level = 3  # default middle

    if expense.store_name:
        matched = Store.query.filter(
            Store.name.ilike(f'%{expense.store_name}%')
        ).first()
        if matched:
            original_store = matched.to_dict()
            original_price_level = matched.average_price_level

    # Find cheaper stores in the same category within radius
    category = expense.category
    cheaper_stores = Store.query.filter(
        Store.category.ilike(f'%{category}%'),
        Store.average_price_level < original_price_level,
    ).all()

    alternatives = []
    for store in cheaper_stores:
        try:
            dist = geodesic(ref_location, (store.lat, store.lng)).km
        except Exception:
            continue

        if dist > radius_km:
            continue

        level_diff = original_price_level - store.average_price_level
        savings_pct = level_diff * SAVINGS_PER_LEVEL
        estimated_saving = round(expense.amount * savings_pct / 100, 2)

        alternatives.append({
            'store': store.to_dict(),
            'distance_km': round(dist, 2),
            'price_level_diff': level_diff,
            'savings_pct': round(savings_pct, 1),
            'estimated_saving': estimated_saving,
        })

    # Sort by estimated saving (descending), then distance (ascending)
    alternatives.sort(key=lambda x: (-x['estimated_saving'], x['distance_km']))
    alternatives = alternatives[:3]  # top 3

    total_saving = sum(a['estimated_saving'] for a in alternatives)

    return {
        'original': {
            'expense': expense.to_dict(),
            'store': original_store,
            'price_level': original_price_level,
        },
        'alternatives': alternatives,
        'total_potential_saving': round(total_saving / max(len(alternatives), 1), 2),
    }
