import os
import asyncio
import httpx
from fastapi import FastAPI

from app.db import Base, engine
from app.routes.health import router as health_router
from app.routes.route_endpoint import router as route_router
from app.routes.intent_endpoint import router as intent_router
from app.routes.telegram_webhook import router as telegram_router
from app.routes.agents_api import router as agents_router
from app.routes.catalog_api import router as catalog_router
from app.routes.session_api import router as session_router
from app.entrypoints.http_api import router as api_router
from app.models import main_models as models          
from app.models import agent_pydantic_models as models_agents 

from app.routes.integrations_stage_d import router as integrator_stage_d_router
from app.routes.integrations_stage_a import router as integrations_router
from app.routes.integrations_stage_b import router as integrations_router_b
from app.routes.services_import import router as services_import_router

# --- ADD THIS IMPORT (from patch) ---
from app.routes.tg_services_add_bridge import router as tg_services_add_router


# --- ENV VARS ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",  
    None            
)

print("TELEGRAM_BOT_TOKEN::", TELEGRAM_BOT_TOKEN)
print("TELEGRAM_WEBHOOK_URL::", TELEGRAM_WEBHOOK_URL)

# --- FASTAPI APP ---
app = FastAPI(title="Router v7 Type-A")

# --- TELEGRAM WEBHOOK SETUP ---
async def set_telegram_webhook():
    """Configure Telegram webhook if token + URL are provided."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_WEBHOOK_URL:
        print("⚠️ Skipping webhook setup (missing TELEGRAM_BOT_TOKEN or WEBHOOK_URL)")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(url, params={"url": TELEGRAM_WEBHOOK_URL})
        try:
            res.raise_for_status()
            print("✅ Telegram webhook set:", res.json())
        except Exception as e:
            print("❌ Failed to set Telegram webhook:", e, res.text)

# --- STARTUP HOOK ---
@app.on_event("startup")
async def startup():
    await asyncio.sleep(2)

    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ensured")
    except Exception as e:
        print("❌ Failed to create DB tables:", e)
    try:
        await set_telegram_webhook()
    except Exception as e:
        print(f"❌ Webhook setup failed: {e}")

app.include_router(health_router)
app.include_router(route_router)
app.include_router(intent_router)
app.include_router(telegram_router)
app.include_router(agents_router)
app.include_router(catalog_router)
app.include_router(session_router)
app.include_router(api_router, prefix="")
app.include_router(integrations_router)
app.include_router(integrations_router_b)
app.include_router(integrator_stage_d_router)
app.include_router(services_import_router)
app.include_router(tg_services_add_router)
