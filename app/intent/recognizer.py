# NEW FILE: app/intents/recognizer.py
# Lightweight intent recognition with add-service guardrail and info-only mapping

def recognize_intent(text: str) -> dict:
    t = (text or "").strip().lower()
    if not t:
        return {"type": "unknown"}

    # Explicit add-service first (avoid misclassifying as browse/list)
    if any(kw in t for kw in [
        "add service", "add a service", "create service",
        "добавить сервис", "добавить услугу",
        "dodaj uslugu", "додати сервіс"
    ]):
        return {"type": "add_service"}

    # Categories / menu trigger
    if t in ("menu", "/menu", "/start", "categories", "what do you have", "what services do you have"):
        return {"type": "show_categories"}

    # Food mapping
    if any(w in t for w in ["food", "restaurant", "restaurants", "eat", "dining", "еда", "ресторан", "рестора"]):
        return {"type": "browse_category", "category": "food"}

    # Transport mapping
    if any(w in t for w in ["transport", "taxi", "bike", "bicycle", "scooter", "транспорт", "такси", "велосипед"]):
        return {"type": "browse_category", "category": "transport"}

    # Booking-like → info-only notice (we don't start booking)
    if any(w in t for w in ["book", "reserve", "reservation", "delivery", "now or later", "доставка", "бронь"]):
        return {"type": "info_only_notice"}

    return {"type": "unknown"}
