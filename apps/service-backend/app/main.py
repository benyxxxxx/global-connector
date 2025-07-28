from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from contextlib import asynccontextmanager
# from app.database import create_db_and_tables

from app.api.router import api_router
from app.config import settings

# from app.core.exceptions import setup_exception_handlers


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code
#     create_db_and_tables()
#     yield
#     # Shutdown code (if needed)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    # lifespan=lifespan,
)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Exception handlers
# setup_exception_handlers(app)

# # Include routers
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
