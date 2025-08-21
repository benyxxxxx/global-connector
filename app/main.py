from fastapi import FastAPI
from app.db import Base, engine
from app.routes.health import router as health_router
from app.routes.route_endpoint import router as route_router
from app.routes.intent_endpoint import router as intent_router
from app.routes.telegram_webhook import router as telegram_router
from app.routes.agents_api import router as agents_router
from app.routes.catalog_api import router as catalog_router
from app.routes.session_api import router as session_router
from app import models                 
from app import models_agents  
import os, httpx, asyncio

Base.metadata.create_all(bind=engine)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("TELEGRAM_BOT_TOKEN:: ", TELEGRAM_BOT_TOKEN)
TELEGRAM_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://router-v7-typea-final.fly.dev/telegram/webhook")
print("TELEGRAM_WEBHOOK_URL:: ", TELEGRAM_WEBHOOK_URL)

app = FastAPI(title="Router v7 Type-A")

async def set_telegram_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    async with httpx.AsyncClient() as client:
        res = await client.post(url, params={"url": TELEGRAM_WEBHOOK_URL})
        print("✅ Webhook set:", res.json())

@app.on_event("startup")
async def startup():
    await asyncio.sleep(3)
    try:
        await set_telegram_webhook()
        print("✅ Webhook set successfully")
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")
Base.metadata.create_all(bind=engine)

app.include_router(health_router)
app.include_router(route_router)
app.include_router(intent_router)
app.include_router(telegram_router)
app.include_router(agents_router)
app.include_router(catalog_router)
app.include_router(session_router)
