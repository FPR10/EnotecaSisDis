"""OCR controller — riconoscimento del vino a partire dalla foto dell'etichetta. Consultazione pubblica.

Pipeline: OcrService (Azure AI Vision) estrae il testo dall'immagine,
TextProcessingService (spaCy + KeyBERT + RapidFuzz) lo confronta col catalogo.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.controller.deps import get_ocr_service, get_text_processing_service
from app.dto.wine_dto import OcrSearchOut, WineOut
from app.service.ocr_service import OcrService, OCRServiceError
from app.service.text_processing_service import TextProcessingService

router = APIRouter()


@router.post("/etichetta", response_model=OcrSearchOut)
async def riconosci_etichetta(
    immagine: UploadFile,
    ocr_service: OcrService = Depends(get_ocr_service),
    text_processing_service: TextProcessingService = Depends(get_text_processing_service),
) -> OcrSearchOut:
    """Estrae il testo dalla foto di un'etichetta e individua il vino corrispondente nel catalogo."""
    contenuto = await immagine.read()
    try:
        testo_estratto = await ocr_service.extract_text(contenuto)
    except OCRServiceError as exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exception)) from exception
    finally:
        ocr_service.close()

    corrispondenze = await text_processing_service.match_wines(testo_estratto)
    return OcrSearchOut(
        extracted_text=testo_estratto,
        results=[WineOut.model_validate(match.wine) for match in corrispondenze],
    )
