from typing import Literal

# Define all possible intents based on your categories
Intent = Literal[
    "food", "sim_card", "real_estate", "surf", "sport", "tourism", "tech", "unknown"
]

# Create keyword lists for each of your 7 categories
KEYWORDS = {
    "food": ["food", "restaurant", "delivery", "eat", "pizza", "burger", "salad"],
    "sim_card": ["sim", "esim", "card", "activate"],
    "real_estate": ["real estate", "rent", "apartment", "house", "lease", "sales"],
    "surf": ["surf", "surfing", "lessons", "gear"],
    "sport": ["sport", "activities", "futsal"],
    "tourism": ["tour", "tourism", "explore", "guided tour"],
    "tech": ["tech", "phone", "computer", "repair"],
}

def detect_intent(text: str) -> Intent:
    """Detects the user's intent by checking for keywords related to each category."""
    t = (text or "").lower()
    for intent, keywords in KEYWORDS.items():
        if any(keyword in t for keyword in keywords):
            return intent
    return "unknown"