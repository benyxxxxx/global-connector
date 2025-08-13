from fastapi import FastAPI
from app.db import Base, engine
from app.routes.health import router as health_router
from app.routes.route_endpoint import router as route_router
from app.routes.telegram_webhook import router as telegram_router

app = FastAPI(title="Router v7 Type-A")
Base.metadata.create_all(bind=engine)

app.include_router(health_router)
app.include_router(route_router)
app.include_router(telegram_router)

