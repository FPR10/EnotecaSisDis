"""
Wine service — logica di business sul catalogo vini.

Orchestrazione delle operazioni di lettura/scrittura sul catalogo esposte dal
WineRepository: ricerca con filtri e paginazione, lettura per id, e operazioni
di scrittura riservate agli admin (creazione, modifica, eliminazione).
"""

from app.config.logging import get_logger
from app.entity.wine_entity import TipoVino, Wine
from app.dto.wine_dto import WineCreate, WineFilter, WineUpdate
from app.repository.wine_repository import WineRepository

logger = get_logger(__name__)


class WineServiceError(Exception):
    """Errore durante un'operazione sul catalogo vini."""


class WineService:
    """
    Wrapper sul WineRepository: espone le operazioni di catalogo (ricerca,
    lettura, scrittura) usate dai controller REST.
    """

    def __init__(self, wine_repository: WineRepository) -> None:
        self.wine_repository = wine_repository

    '''
    OPERAZIONI DI LETTURA
    '''

    async def get_vino(self, wine_id: str) -> Wine:
        """Recupera un vino per id; solleva errore se non presente in catalogo."""
        vino = await self.wine_repository.find_by_id(wine_id)
        if vino is None:
            raise WineServiceError(f"Vino con id {wine_id} non trovato")
        return vino

    async def cerca_vini(
        self, filtri: WineFilter, skip: int = 0, limit: int = 20
    ) -> tuple[list[Wine], int]:
        """Restituisce i vini che soddisfano i filtri, col conteggio totale per la paginazione."""
        vini = await self.wine_repository.find_all(filtri, skip=skip, limit=limit)
        totale = await self.wine_repository.count(filtri)
        return vini, totale

    async def vini_per_tipo(self, tipo: TipoVino) -> list[Wine]:
        return await self.wine_repository.find_by_tipo(tipo)

    async def vini_per_regione(self, regione: str) -> list[Wine]:
        return await self.wine_repository.find_by_regione(regione)

    async def regioni_per_tipo(self, tipo: TipoVino) -> list[str]:
        return await self.wine_repository.get_regioni_by_tipo(tipo)

    '''
    OPERAZIONI DI SCRITTURA (solo per utente ADMIN)
    '''

    async def crea_vino(self, dati: WineCreate) -> Wine:
        """Crea un nuovo vino nel catalogo a partire dai dati validati dal DTO."""
        vino = Wine(**dati.model_dump())
        return await self.wine_repository.save(vino)

    async def aggiorna_vino(self, wine_id: str, dati: WineUpdate) -> Wine:
        """Aggiorna un vino esistente; solleva errore se l'id non esiste in catalogo."""
        vino = await self.get_vino(wine_id)
        return await self.wine_repository.update(vino, dati)

    async def elimina_vino(self, wine_id: str) -> None:
        """Elimina un vino dal catalogo; solleva errore se l'id non esiste."""
        vino = await self.get_vino(wine_id)
        await self.wine_repository.delete(vino)
