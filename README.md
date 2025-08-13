# Router v7 (Type-A, final)

What’s included:
- `/health` — liveness
- `/route` — n8n-style shim (returns `{handled, output}`)
- `/telegram/webhook` — ingest updates and **reply asynchronously**
- **Service Agent** with two flows:
  - **Food flow**: list → Visit/Delivery → if Delivery → "Now or later?" → create booking → promo code surfaced
  - **Real estate** (short-term vs long-term) — branches with placeholders
- **SQLite persistence** for bookings (`data/app.db`)
- Minimal Telegram client using `httpx`
- Smoke test instructions in `smoke_test.txt`

## Run
```
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="123456:ABC..."           
export GLOBAL_PROMO_CODE="WELCOME10"                
uvicorn app.main:app --reload --port 8080
```

## Contract
- **/route** (POST): `{ "message": "...", "user_id": "123", "session": { "session_id": "..." } }`
  - Response: `{ "handled": true|false, "output": "..." }`

- **/telegram/webhook** (POST): Telegram update JSON
  - Returns `{"ok": true, "handled": bool}` and sends message back asynchronously.

## Notes
- Booking data is persisted via SQLite.
- Conversation state is in-memory per process. For durable state, swap to Redis or a table.
