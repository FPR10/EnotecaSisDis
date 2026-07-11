"""
Blob Storage service — upload di file su Azure Blob Storage.

Utilizzato per:
- immagini etichette dei vini (URL del blob viene salvato in Wine.immagine_etichetta, al posto del file reale)
- audit dei file CSV/JSON caricati per l'import massivo
"""

import asyncio
import uuid
from datetime import datetime, timezone

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient, ContentSettings

from app.config.logging import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)

tipi_file = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "csv": "text/csv",
    "json": "application/json",
}


class BlobStorageServiceError(Exception):
    """Errore durante un'operazione su Azure Blob Storage."""


class BlobStorageService:
    """
    Wrapper su Azure Blob Storage. Il client (da SDK) è sincrono: le chiamate vengono
    eseguite in un thread separato per non bloccare l'event loop di FastAPI.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.azure_storage_connection_string:
            raise BlobStorageServiceError(
                "Azure Blob Storage non configurato: impostare AZURE_STORAGE_CONNECTION_STRING"
            )

        self._client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self._container_etichette = settings.azure_storage_container_etichette
        self._container_audit = settings.azure_storage_container_audit

    async def upload_etichetta(self, contenuto: bytes, wine_id: str, nome_file: str) -> str:
        """Carica l'immagine di un'etichetta e restituisce l'URL pubblico del blob."""
        estensione = self._estensione(nome_file, default="jpg")
        nome_blob = f"{wine_id}/{uuid.uuid4().hex}.{estensione}"
        return await self._upload(self._container_etichette, nome_blob, contenuto, estensione)

    async def upload_audit_import(self, contenuto: bytes, nome_file: str, admin_email: str) -> str:
        """Conserva una copia del file CSV/JSON caricato per l'import massivo, ai fini di audit/reimport."""
        estensione = self._estensione(nome_file, default="csv")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        nome_blob = f"{timestamp}_{admin_email}_{nome_file or f'import.{estensione}'}"
        return await self._upload(self._container_audit, nome_blob, contenuto, estensione)

    async def _upload(self, container: str, nome_blob: str, contenuto: bytes, estensione: str) -> str:
        blob_client = self._client.get_blob_client(container=container, blob=nome_blob)
        content_settings = ContentSettings(content_type=tipi_file.get(estensione, "application/octet-stream"))

        try:
            await asyncio.to_thread(
                blob_client.upload_blob,
                contenuto,
                overwrite=True,
                content_settings=content_settings,
            )
        except HttpResponseError as exception:
            logger.error(f"Azure Blob Storage: upload fallito su container '{container}': {exception}")
            raise BlobStorageServiceError("Upload su Blob Storage fallito") from exception

        return blob_client.url

    @staticmethod
    def _estensione(nome_file: str, default: str) -> str:
        return nome_file.rsplit(".", 1)[-1].lower() if nome_file and "." in nome_file else default

    def close(self) -> None:
        """Chiude la connessione HTTP del client Azure."""
        self._client.close()
