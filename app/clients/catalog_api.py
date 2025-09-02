# NEW FILE: app/clients/catalog_api.py

from __future__ import annotations
from typing import List, Dict
from app.clients import backend_api as be

class CatalogAPI:
    @staticmethod
    def get_non_empty_categories() -> List[str]:
        # Implement or map to your backend.
        # Expected: returns only categories that currently have items.
        try:
            return be.get_non_empty_categories()
        except AttributeError:
            # TEMP fallback for manual testing
            return ["food", "transport"]

    @staticmethod
    def list_services_by_category(category_key: str) -> List[Dict]:
        # Implement or map to your backend.
        try:
            return be.list_services_by_category(category_key)
        except AttributeError:
            # TEMP fallback for manual testing
            if category_key == "food":
                return [
                    {"name": "Pizza Place", "description": "Best slices. https://t.me/pizzaplace_bot", "price_hint": "$$", "promo_code": "SLICE10"},
                    {"name": "Sushi Bar", "description": "Fresh nigiri.", "price_hint": "$$$"},
                    {"name": "Burger Truck", "description": "Smash burgers at the park."},
                    {"name": "Pasta Corner", "description": "Homemade pasta daily."},
                    {"name": "Vegan Deli", "description": "Plant-based goodies."},
                    {"name": "Curry House", "description": "Spicy!"}
                ]
            if category_key == "transport":
                return [
                    {"name": "City Taxi", "description": "Call a cab. https://example.com/taxi"},
                    {"name": "Bike Rentals", "description": "Hourly rentals near you."},
                ]
            return []
