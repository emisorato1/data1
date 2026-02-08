from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infrastructure.db.seed import seed_defaults, seed_default_tenant
from app.infrastructure.db.session import AsyncSessionLocal
from app.presentation.http.routes.auth import router as auth_router
from app.presentation.http.routes.health import router as health_router
from app.presentation.http.routes.messages import router as messages_router
from app.presentation.http.routes.chat import router as chat_router
from app.presentation.http.routes.access_test import router as access_test_router

# Langfuse observability
from app.infrastructure.observability.langfuse_client import init_langfuse, flush_langfuse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar Langfuse al startup si está habilitado
    init_langfuse()
    
    async with AsyncSessionLocal() as db:
        await seed_defaults(db)
        await seed_default_tenant(db)
    yield
    
    # Flush traces pendientes al shutdown
    flush_langfuse()


app = FastAPI(
    title="Enterprise AI Platform - API Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(messages_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(access_test_router, prefix=settings.API_PREFIX)
