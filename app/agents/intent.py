from typing import Literal

Intent = Literal["food", "real_estate", "unknown"]

FOOD_KW = ["food", "pizza", "eat", "restaurant", "hungry", "order", "delivery"]
RE_KW = ["rent", "buy", "apartment", "flat", "house", "real estate", "lease", "short-term", "short term", "long-term", "long term"]

def detect_intent(text: str) -> Intent:
    t = (text or "").lower()
    if any(k in t for k in FOOD_KW):
        return "food"
    if any(k in t for k in RE_KW):
        return "real_estate"
    return "unknown"
