"""
Wine service — logica di business sul catalogo vini.

Orchestrazione delle operazioni di lettura/scrittura sul catalogo esposte dal
WineRepository: ricerca con filtri e paginazione, lettura per id, e operazioni
di scrittura riservate agli admin (creazione, modifica, eliminazione).
"""

import csv
import io
import json

from pydantic import ValidationError

from app.config.logging import get_logger
from app.entity.wine_entity import TipoVino, Wine
from app.dto.wine_dto import BulkImportResult, WineCreate, WineFilter, WineUpdate
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

    async def aggiorna_immagine_etichetta(self, wine_id: str, url: str) -> Wine:
        """Aggiorna l'URL dell'immagine etichetta (su Blob Storage) di un vino esistente."""
        vino = await self.get_vino(wine_id)
        return await self.wine_repository.update(vino, WineUpdate(immagine_etichetta=url))

    async def importa_vini_da_file(self, contenuto: bytes, nome_file: str) -> BulkImportResult:
        """
        Crea più vini a partire da un file CSV o JSON (formato dedotto dall'estensione).
        Le righe non valide vengono scartate e riportate in BulkImportResult.errors,
        senza interrompere l'importazione delle altre.
        """
        righe = self._estrai_righe(contenuto, nome_file)

        creati = 0
        errori: list[dict] = []
        for indice, riga in enumerate(righe, start=1):
            try:
                dati = WineCreate(**riga)
            except ValidationError as exception:
                errori.append({"riga": indice, "errore": str(exception)})
                continue
            try:
                await self.crea_vino(dati)
                creati += 1
            except Exception as exception:
                errori.append({"riga": indice, "errore": str(exception)})

        return BulkImportResult(created=creati, errors=errori)

    @staticmethod
    def _estrai_righe(contenuto: bytes, nome_file: str) -> list[dict]:
        """Effettua il parsing del file (CSV o JSON) in una lista di dizionari grezzi."""
        estensione = nome_file.rsplit(".", 1)[-1].lower() if "." in nome_file else ""

        if estensione == "json":
            dati = json.loads(contenuto.decode("utf-8"))
            if not isinstance(dati, list):
                raise WineServiceError("Il file JSON deve contenere una lista di vini")
            return dati

        if estensione == "csv":
            testo = contenuto.decode("utf-8-sig")
            righe = csv.DictReader(io.StringIO(testo))
            # le celle vuote vengono escluse, così i campi opzionali restano None invece di "" non valido
            return [
                {chiave: valore for chiave, valore in riga.items() if valore not in (None, "")}
                for riga in righe
            ]

        raise WineServiceError("Formato file non supportato: usare un file .csv o .json")
