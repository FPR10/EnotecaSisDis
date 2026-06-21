"""Pairing controller — abbinamento cibo-vino generato da Groq (Llama). Consultazione pubblica."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.controller.deps import get_pairing_service
from app.dto.wine_dto import AbbinamentoCiboIn, AbbinamentoOut, VinoSuggerito, WineOut
from app.service.pairing_service import PairingService, PairingServiceError

router = APIRouter()


@router.post("/abbinamento", response_model=AbbinamentoOut)
async def abbina_cibo_vino(
    dati: AbbinamentoCiboIn,
    pairing_service: PairingService = Depends(get_pairing_service),
) -> AbbinamentoOut:
    """Suggerisce i vini del catalogo più adatti al piatto descritto."""
    try:
        risultati = await pairing_service.suggerisci_vini(dati.cibo)
    except PairingServiceError as exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exception)) from exception

    suggerimenti = [
        VinoSuggerito(wine=WineOut.model_validate(wine), motivazione=motivazione)
        for wine, motivazione in risultati
    ]
    return AbbinamentoOut(cibo=dati.cibo, suggerimenti=suggerimenti)
