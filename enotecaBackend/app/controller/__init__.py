from app.controller.auth_controller import router as auth_router
from app.controller.ocr_controller import router as ocr_router
from app.controller.pairing_controller import router as pairing_router
from app.controller.wine_controller import router as wine_router

__all__ = [
    "auth_router",
    "ocr_router",
    "pairing_router",
    "wine_router",
]
