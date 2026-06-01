from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.config.logging import setup_logging, get_logger
from app.controller import wine_router, auth_router

settings = get_settings()
setup_logging(debug=settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Avvio {settings.app_name} v{settings.app_version}")
    yield
    logger.info("Shutdown applicazione")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router ---
app.include_router(auth_router,  prefix="/api/v1/auth",  tags=["auth"])
app.include_router(wine_router,  prefix="/api/v1/wines", tags=["wines"])


@app.get("/health", tags=["system"])
async def health_check():
    """Healthcheck per Azure App Service."""
    return {"status": "ok", "version": settings.app_version}
