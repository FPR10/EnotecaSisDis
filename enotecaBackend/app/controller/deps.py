"""Dependency provider FastAPI: costruiscono repository e service per i controller."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repository.user_repository import UserRepository
from app.repository.wine_repository import WineRepository
from app.service.authentication_service import AuthenticationService
from app.service.blob_storage_service import BlobStorageService
from app.service.ocr_service import OcrService
from app.service.pairing_service import PairingService
from app.service.text_processing_service import TextProcessingService
from app.service.wine_service import WineService


def get_wine_repository(db: AsyncSession = Depends(get_db)) -> WineRepository:
    return WineRepository(db)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_wine_service(
    wine_repository: WineRepository = Depends(get_wine_repository),
) -> WineService:
    return WineService(wine_repository)


def get_authentication_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthenticationService:
    return AuthenticationService(user_repository)


def get_pairing_service(
    wine_repository: WineRepository = Depends(get_wine_repository),
) -> PairingService:
    return PairingService(wine_repository)


def get_text_processing_service(
    wine_repository: WineRepository = Depends(get_wine_repository),
) -> TextProcessingService:
    return TextProcessingService(wine_repository)


def get_ocr_service() -> OcrService:
    return OcrService()


def get_blob_storage_service() -> BlobStorageService:
    return BlobStorageService()
