"""
OCR service - primo stadio della pipeline di riconoscimento dell'immagine.

In questa classe di legge il testo dalle etichette mediante Azure AI Visione
"""

import asyncio

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from app.config.logging import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)


class OCRServiceError(Exception):
    """Errore durante l'estrazione del testo dall'immagine dell'etichetta."""


class OcrService:
    """
    Wrapper su Azure AI Vision (Read OCR) per l'estrazione del testo
    dalle foto delle etichette dei vini caricate dall'utente.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.azure_vision_endpoint or not settings.azure_vision_key:
            raise OCRServiceError(
                "Azure AI Vision non configurato: impostare "
                "AZURE_VISION_ENDPOINT e AZURE_VISION_KEY"
            )

        self._client = ImageAnalysisClient(
            endpoint=settings.azure_vision_endpoint,
            credential=AzureKeyCredential(settings.azure_vision_key),
        )

    async def extract_text(self, image_bytes: bytes) -> str:
        """
        Esegue il la lettura dell'immagine dell'etichetta
        e restituisce il testo individuato (una riga per ogni riga rilevata).

        Il client è sincrono: l'analisi viene eseguita in un thread
        separato per non bloccare l'event loop di FastAPI.
        """
        if not image_bytes:
            raise OCRServiceError("Immagine vuota: nessun contenuto da analizzare")

        try:
            result = await asyncio.to_thread(
                self._client.analyze,   #effettua l'analisi dell'immagine
                image_data=image_bytes,
                visual_features=[VisualFeatures.READ],
            )
        except HttpResponseError as exception:
            logger.error(f"Azure AI Vision: analisi etichetta fallita: {exception}")
            raise OCRServiceError("Estrazione OCR dall'etichetta fallita") from exception

        if result.read is None:
            return ""

        extracted_lines = []
        
        for block in result.read.blocks:
            for line in block.lines:
                extracted_lines.append(line.text)
                
        logger.debug(f"OCR: estratte {len(extracted_lines)} righe di testo dall'etichetta")
        
        return "\n".join(extracted_lines)


    def close(self) -> None:
        """Chiude la connessione HTTP del client Azure."""
        self._client.close()
