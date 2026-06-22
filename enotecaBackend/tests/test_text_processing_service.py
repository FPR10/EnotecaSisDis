"""
Unit test per TextProcessingService.

I modelli pesanti (spaCy, KeyBERT) vengono mockati tramite le funzioni di
caricamento `_load_spacy_model`/`_load_keybert_model`: i test non scaricano né
caricano alcun modello reale. Il fuzzy matching (RapidFuzz) invece NON è
mockato, per verificare il comportamento reale dell'algoritmo di matching.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.entity.wine_entity import TipoVino, Wine
from app.service.text_processing_service import TextProcessingService


def make_wine(**overrides) -> Wine:
    dati = dict(
        id="wine-1",
        nome="Barolo",
        produttore="Cantina Rossi",
        azienda_vinicola="Cantina Rossi",
        regione="Piemonte",
        tipo=TipoVino.ROSSO,
        vitigno="Nebbiolo",
        denominazione="DOCG",
    )
    dati.update(overrides)
    return Wine(**dati)


@pytest.fixture
def repository():
    return AsyncMock()


@pytest.fixture
def service(repository):
    with patch("app.service.text_processing_service._load_spacy_model") as load_spacy, \
         patch("app.service.text_processing_service._load_keybert_model") as load_keybert:
        load_spacy.return_value = MagicMock()
        load_keybert.return_value = MagicMock()
        return TextProcessingService(repository)


class TestExtractEntities:
    def test_keeps_only_relevant_entity_labels(self, service):
        doc = SimpleNamespace(ents=[
            SimpleNamespace(text="Cantina Rossi", label_="ORG"),
            SimpleNamespace(text="Piemonte", label_="LOC"),
            SimpleNamespace(text="2019", label_="DATE"),
        ])
        service._nlp.return_value = doc

        risultato = service.extract_entities("testo etichetta")

        assert risultato == ["Cantina Rossi", "Piemonte"]


class TestExtractKeywords:
    def test_returns_empty_list_for_blank_text(self, service):
        risultato = service.extract_keywords("   ")

        assert risultato == []
        service._keybert.extract_keywords.assert_not_called()

    def test_returns_keywords_without_scores(self, service):
        service._keybert.extract_keywords.return_value = [("barolo", 0.8), ("piemonte", 0.6)]

        risultato = service.extract_keywords("testo", top_n=5)

        assert risultato == ["barolo", "piemonte"]
        assert service._keybert.extract_keywords.call_args.kwargs["top_n"] == 5


class TestMatchWines:
    @pytest.mark.asyncio
    async def test_returns_empty_for_blank_text(self, service, repository):
        risultato = await service.match_wines("   ")

        assert risultato == []
        repository.find_all_for_matching.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_candidates(self, service, repository):
        repository.find_all_for_matching.return_value = []
        service._nlp.return_value = SimpleNamespace(ents=[])
        service._keybert.extract_keywords.return_value = []

        risultato = await service.match_wines("Barolo Cantina Rossi")

        assert risultato == []

    @pytest.mark.asyncio
    async def test_finds_matching_wine_via_entities_and_keywords(self, service, repository):
        candidati = [
            make_wine(id="wine-1", nome="Barolo", produttore="Cantina Rossi"),
            make_wine(id="wine-2", nome="Chianti", produttore="Cantina Bianchi", azienda_vinicola="Cantina Bianchi", vitigno="Sangiovese", denominazione="DOCG"),
        ]
        repository.find_all_for_matching.return_value = candidati
        service._nlp.return_value = SimpleNamespace(ents=[SimpleNamespace(text="Cantina Rossi", label_="ORG")])
        service._keybert.extract_keywords.return_value = [("Barolo", 0.9)]

        risultati = await service.match_wines("Barolo Cantina Rossi 2019")

        assert risultati[0].wine.id == "wine-1"
        assert risultati[0].score >= 60.0

    @pytest.mark.asyncio
    async def test_falls_back_to_full_text_when_no_salient_terms(self, service, repository):
        candidati = [make_wine(id="wine-1", nome="Barolo Cantina Rossi")]
        repository.find_all_for_matching.return_value = candidati
        service._nlp.return_value = SimpleNamespace(ents=[])
        service._keybert.extract_keywords.return_value = []

        risultati = await service.match_wines("Barolo Cantina Rossi")

        assert len(risultati) == 1
        assert risultati[0].wine.id == "wine-1"

    @pytest.mark.asyncio
    async def test_filters_out_low_score_matches(self, service, repository):
        candidati = [
            make_wine(
                id="wine-1",
                nome="Totalmente Diverso",
                produttore="Altra Cantina",
                azienda_vinicola="Altra Cantina",
                regione="Sicilia",
                vitigno=None,
                denominazione=None,
            )
        ]
        repository.find_all_for_matching.return_value = candidati
        service._nlp.return_value = SimpleNamespace(ents=[])
        service._keybert.extract_keywords.return_value = []

        risultati = await service.match_wines("xyz9 query senza alcuna somiglianza qwerty")

        assert risultati == []

    @pytest.mark.asyncio
    async def test_respects_limit(self, service, repository):
        candidati = [make_wine(id=f"wine-{i}", nome="Barolo Cantina Rossi") for i in range(5)]
        repository.find_all_for_matching.return_value = candidati
        service._nlp.return_value = SimpleNamespace(ents=[])
        service._keybert.extract_keywords.return_value = []

        risultati = await service.match_wines("Barolo Cantina Rossi", limit=2)

        assert len(risultati) == 2

    @pytest.mark.asyncio
    async def test_results_sorted_by_score_descending(self, service, repository):
        candidati = [
            make_wine(id="wine-esatto", nome="Barolo Cantina Rossi"),
            make_wine(id="wine-parziale", nome="Barolo", produttore="Altra Azienda", azienda_vinicola="Altra Azienda"),
        ]
        repository.find_all_for_matching.return_value = candidati
        service._nlp.return_value = SimpleNamespace(ents=[])
        service._keybert.extract_keywords.return_value = []

        risultati = await service.match_wines("Barolo Cantina Rossi")

        assert risultati == sorted(risultati, key=lambda match: match.score, reverse=True)
