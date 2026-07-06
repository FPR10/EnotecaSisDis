from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.config.logging import setup_logging, get_logger
from app.controller import auth_router, ocr_router, pairing_router, wine_router

settings = get_settings()
setup_logging(debug=settings.debug)
logger = get_logger(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:4200",
    "https://enoteca-backend.whitebush-b41f9777.westeurope.azurecontainerapps.io"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Avvio {settings.app_name} v{settings.app_version}")
    # Preload modelli NLP al'avvio per evitare cold start sulla prima richiesta OCR
    from app.service.text_processing_service import _load_spacy_model, _load_keybert_model
    logger.info("Caricamento modelli NLP in corso...")
    _load_spacy_model()
    _load_keybert_model()
    logger.info("Modelli NLP caricati")
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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Gestione errori non previsti ---
# Senza questo handler, un'eccezione non gestita arriva al client come risposta
# 500 testuale senza corpo JSON: il frontend non può estrarre alcun messaggio
# e lo stack trace reale resta visibile solo nei log del server.
#
# Nota: un handler su Exception (a differenza di HTTPException) viene eseguito da
# ServerErrorMiddleware, che sta FUORI da CORSMiddleware nello stack di Starlette.
# Per questo la risposta non riceve gli header CORS aggiunti normalmente dal middleware,
# e il browser la blocca prima che il frontend possa leggerla: li aggiungiamo a mano.
@app.exception_handler(Exception)
async def gestione_errori_non_previsti(request: Request, exception: Exception) -> JSONResponse:
    logger.error(f"Errore non gestito su {request.method} {request.url.path}: {exception}", exc_info=True)
    response = JSONResponse(status_code=500, content={"detail": "Errore interno del server. Riprova più tardi."})
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# --- Router ---
app.include_router(auth_router,    prefix="/api/v1/auth",    tags=["auth"])
app.include_router(wine_router,    prefix="/api/v1/wines",   tags=["wines"])
app.include_router(pairing_router, prefix="/api/v1/pairing", tags=["pairing"])
app.include_router(ocr_router,     prefix="/api/v1/ocr",     tags=["ocr"])


@app.get("/health", tags=["system"])
async def health_check():
    """Healthcheck per Azure App Service."""
    return {"status": "ok", "version": settings.app_version}
