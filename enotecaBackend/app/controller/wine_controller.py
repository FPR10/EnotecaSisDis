"""Wine controller — consultazione del catalogo (pubblica) e gestione (solo admin)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.security import require_admin
from app.controller.deps import get_wine_service
from app.dto.wine_dto import WineCreate, WineFilter, WineOut, WinePageOut, WineUpdate
from app.entity.user_entity import User
from app.entity.wine_entity import TipoVino
from app.service.wine_service import WineService, WineServiceError

router = APIRouter()


@router.get("", response_model=WinePageOut)
async def cerca_vini(
    filtri: WineFilter = Depends(),
    skip: int = 0,
    limit: int = 20,
    wine_service: WineService = Depends(get_wine_service),
) -> WinePageOut:
    """Lista vini del catalogo, filtrabile e paginata. Consultazione pubblica."""
    vini, totale = await wine_service.cerca_vini(filtri, skip=skip, limit=limit)
    return WinePageOut(
        items=[WineOut.model_validate(vino) for vino in vini],
        total=totale,
        skip=skip,
        limit=limit,
    )


@router.get("/regioni", response_model=list[str])
async def get_regioni_per_tipo(
    tipo: TipoVino,
    wine_service: WineService = Depends(get_wine_service),
) -> list[str]:
    """Regioni distinte presenti in catalogo per una data tipologia (per i filtri del frontend)."""
    return await wine_service.regioni_per_tipo(tipo)


@router.get("/{wine_id}", response_model=WineOut)
async def get_vino(
    wine_id: str,
    wine_service: WineService = Depends(get_wine_service),
) -> WineOut:
    """Dettaglio di un singolo vino. Consultazione pubblica."""
    try:
        vino = await wine_service.get_vino(wine_id)
    except WineServiceError as exception:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exception)) from exception
    return WineOut.model_validate(vino)


@router.post("", response_model=WineOut, status_code=status.HTTP_201_CREATED)
async def crea_vino(
    dati: WineCreate,
    wine_service: WineService = Depends(get_wine_service),
    _admin: User = Depends(require_admin),
) -> WineOut:
    """Crea un nuovo vino nel catalogo. Riservato agli admin."""
    vino = await wine_service.crea_vino(dati)
    return WineOut.model_validate(vino)


@router.put("/{wine_id}", response_model=WineOut)
async def aggiorna_vino(
    wine_id: str,
    dati: WineUpdate,
    wine_service: WineService = Depends(get_wine_service),
    _admin: User = Depends(require_admin),
) -> WineOut:
    """Aggiorna un vino esistente. Riservato agli admin."""
    try:
        vino = await wine_service.aggiorna_vino(wine_id, dati)
    except WineServiceError as exception:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exception)) from exception
    return WineOut.model_validate(vino)


@router.delete("/{wine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def elimina_vino(
    wine_id: str,
    wine_service: WineService = Depends(get_wine_service),
    _admin: User = Depends(require_admin),
) -> None:
    """Elimina un vino dal catalogo. Riservato agli admin."""
    try:
        await wine_service.elimina_vino(wine_id)
    except WineServiceError as exception:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exception)) from exception
