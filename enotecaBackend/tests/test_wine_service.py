"""
Unit test per WineService.

Il WineRepository viene mockato (AsyncMock): i test non toccano alcun database
reale e verificano solo la logica di business del service.
"""

import json
from unittest.mock import AsyncMock

import pytest

from app.dto.wine_dto import BulkImportResult, WineFilter, WineUpdate
from app.entity.wine_entity import TipoVino, Wine
from app.service.wine_service import WineService, WineServiceError


def make_wine(**overrides) -> Wine:
    dati = dict(
        id="wine-1",
        nome="Barolo",
        produttore="Cantina X",
        azienda_vinicola="Cantina X",
        regione="Piemonte",
        tipo=TipoVino.ROSSO,
        disponibile=True,
        prezzo=25.0,
    )
    dati.update(overrides)
    return Wine(**dati)


@pytest.fixture
def repository():
    return AsyncMock()


@pytest.fixture
def service(repository):
    return WineService(repository)


class TestGetVino:
    @pytest.mark.asyncio
    async def test_returns_wine_when_found(self, service, repository):
        repository.find_by_id.return_value = make_wine()

        vino = await service.get_vino("wine-1")

        assert vino.id == "wine-1"
        repository.find_by_id.assert_awaited_once_with("wine-1")

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, service, repository):
        repository.find_by_id.return_value = None

        with pytest.raises(WineServiceError):
            await service.get_vino("missing")


class TestCercaVini:
    @pytest.mark.asyncio
    async def test_returns_wines_and_total(self, service, repository):
        repository.find_all.return_value = [make_wine(), make_wine(id="wine-2")]
        repository.count.return_value = 2

        vini, totale = await service.cerca_vini(WineFilter(), skip=0, limit=20)

        assert len(vini) == 2
        assert totale == 2


class TestCreaVino:
    @pytest.mark.asyncio
    async def test_saves_wine_built_from_dto(self, service, repository):
        from app.dto.wine_dto import WineCreate

        repository.save.side_effect = lambda wine: wine
        dati = WineCreate(
            nome="Chianti",
            produttore="Cantina Y",
            azienda_vinicola="Cantina Y",
            regione="Toscana",
            tipo=TipoVino.ROSSO,
        )

        vino = await service.crea_vino(dati)

        assert vino.nome == "Chianti"
        repository.save.assert_awaited_once()


class TestAggiornaVino:
    @pytest.mark.asyncio
    async def test_updates_existing_wine(self, service, repository):
        esistente = make_wine()
        repository.find_by_id.return_value = esistente
        repository.update.return_value = esistente

        await service.aggiorna_vino("wine-1", WineUpdate(prezzo=30.0))

        repository.update.assert_awaited_once_with(esistente, WineUpdate(prezzo=30.0))

    @pytest.mark.asyncio
    async def test_raises_when_wine_missing(self, service, repository):
        repository.find_by_id.return_value = None

        with pytest.raises(WineServiceError):
            await service.aggiorna_vino("missing", WineUpdate(prezzo=30.0))


class TestEliminaVino:
    @pytest.mark.asyncio
    async def test_deletes_existing_wine(self, service, repository):
        esistente = make_wine()
        repository.find_by_id.return_value = esistente

        await service.elimina_vino("wine-1")

        repository.delete.assert_awaited_once_with(esistente)

    @pytest.mark.asyncio
    async def test_raises_when_wine_missing(self, service, repository):
        repository.find_by_id.return_value = None

        with pytest.raises(WineServiceError):
            await service.elimina_vino("missing")


class TestAggiornaImmagineEtichetta:
    @pytest.mark.asyncio
    async def test_updates_immagine_etichetta(self, service, repository):
        esistente = make_wine()
        repository.find_by_id.return_value = esistente
        repository.update.return_value = esistente

        await service.aggiorna_immagine_etichetta("wine-1", "https://blob/etichetta.jpg")

        dati_passati = repository.update.call_args.args[1]
        assert dati_passati.immagine_etichetta == "https://blob/etichetta.jpg"

    @pytest.mark.asyncio
    async def test_raises_when_wine_missing(self, service, repository):
        repository.find_by_id.return_value = None

        with pytest.raises(WineServiceError):
            await service.aggiorna_immagine_etichetta("missing", "https://blob/etichetta.jpg")


class TestImportaViniDaFile:
    @pytest.mark.asyncio
    async def test_json_import_creates_all_valid_wines(self, service, repository):
        repository.save.side_effect = lambda wine: wine
        righe = [
            {
                "nome": "Barolo",
                "produttore": "Cantina X",
                "azienda_vinicola": "Cantina X",
                "regione": "Piemonte",
                "tipo": "rosso",
            },
            {
                "nome": "Greco di Tufo",
                "produttore": "Cantina Y",
                "azienda_vinicola": "Cantina Y",
                "regione": "Campania",
                "tipo": "bianco",
            },
        ]
        contenuto = json.dumps(righe).encode("utf-8")

        risultato = await service.importa_vini_da_file(contenuto, "vini.json")

        assert risultato == BulkImportResult(created=2, errors=[])
        assert repository.save.await_count == 2

    @pytest.mark.asyncio
    async def test_json_import_collects_validation_errors(self, service, repository):
        repository.save.side_effect = lambda wine: wine
        righe = [
            {
                "nome": "Barolo",
                "produttore": "Cantina X",
                "azienda_vinicola": "Cantina X",
                "regione": "Piemonte",
                "tipo": "rosso",
            },
            {"nome": "Vino senza campi obbligatori"},
        ]
        contenuto = json.dumps(righe).encode("utf-8")

        risultato = await service.importa_vini_da_file(contenuto, "vini.json")

        assert risultato.created == 1
        assert len(risultato.errors) == 1
        assert risultato.errors[0]["riga"] == 2

    @pytest.mark.asyncio
    async def test_csv_import_creates_wines(self, service, repository):
        repository.save.side_effect = lambda wine: wine
        contenuto = (
            "nome,produttore,azienda_vinicola,regione,tipo\n"
            "Barolo,Cantina X,Cantina X,Piemonte,rosso\n"
            "Greco di Tufo,Cantina Y,Cantina Y,Campania,bianco\n"
        ).encode("utf-8")

        risultato = await service.importa_vini_da_file(contenuto, "vini.csv")

        assert risultato == BulkImportResult(created=2, errors=[])

    @pytest.mark.asyncio
    async def test_csv_empty_cells_treated_as_optional_none(self, service, repository):
        repository.save.side_effect = lambda wine: wine
        contenuto = (
            "nome,produttore,azienda_vinicola,regione,tipo,annata\n"
            "Barolo,Cantina X,Cantina X,Piemonte,rosso,\n"
        ).encode("utf-8")

        risultato = await service.importa_vini_da_file(contenuto, "vini.csv")

        assert risultato.created == 1
        assert risultato.errors == []

    @pytest.mark.asyncio
    async def test_unsupported_extension_raises(self, service, repository):
        with pytest.raises(WineServiceError):
            await service.importa_vini_da_file(b"qualcosa", "vini.txt")

    @pytest.mark.asyncio
    async def test_json_not_a_list_raises(self, service, repository):
        contenuto = json.dumps({"nome": "Barolo"}).encode("utf-8")

        with pytest.raises(WineServiceError):
            await service.importa_vini_da_file(contenuto, "vini.json")

    @pytest.mark.asyncio
    async def test_save_error_is_collected_not_raised(self, service, repository):
        repository.save.side_effect = RuntimeError("DB down")
        righe = [
            {
                "nome": "Barolo",
                "produttore": "Cantina X",
                "azienda_vinicola": "Cantina X",
                "regione": "Piemonte",
                "tipo": "rosso",
            }
        ]
        contenuto = json.dumps(righe).encode("utf-8")

        risultato = await service.importa_vini_da_file(contenuto, "vini.json")

        assert risultato.created == 0
        assert len(risultato.errors) == 1
        assert risultato.errors[0]["riga"] == 1
