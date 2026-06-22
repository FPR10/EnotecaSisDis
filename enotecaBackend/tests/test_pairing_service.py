"""
Unit test per PairingService.

Il client Groq (AsyncGroq) e il WineRepository vengono mockati: i test non
fanno alcuna chiamata di rete e non richiedono una API key reale.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from groq import APIError as GroqAPIError

from app.entity.wine_entity import TipoVino, Wine
from app.service.pairing_service import PairingService, PairingServiceError


def make_settings(api_key="fake-groq-key", model="llama-3.3-70b-versatile"):
    return SimpleNamespace(groq_api_key=api_key, groq_model=model)


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


def make_groq_response(content: str):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


@pytest.fixture
def repository():
    return AsyncMock()


@pytest.fixture
def mock_groq_client():
    with patch("app.service.pairing_service.AsyncGroq") as client_class:
        instance = MagicMock()
        instance.chat.completions.create = AsyncMock()
        client_class.return_value = instance
        yield instance


@pytest.fixture
def service(repository, mock_groq_client):
    with patch("app.service.pairing_service.get_settings", return_value=make_settings()):
        return PairingService(repository)


class TestInit:
    def test_raises_when_api_key_missing(self, repository, mock_groq_client):
        with patch(
            "app.service.pairing_service.get_settings",
            return_value=make_settings(api_key=""),
        ):
            with pytest.raises(PairingServiceError):
                PairingService(repository)

    def test_builds_client_with_api_key(self, repository, mock_groq_client):
        settings = make_settings()
        with patch("app.service.pairing_service.get_settings", return_value=settings), \
             patch("app.service.pairing_service.AsyncGroq") as client_class:
            PairingService(repository)

        assert client_class.call_args.kwargs["api_key"] == settings.groq_api_key


class TestSuggerisciVini:
    @pytest.mark.asyncio
    async def test_raises_on_empty_cibo(self, service, repository):
        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("   ")

        repository.find_all_for_matching.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_raises_when_no_wines_available(self, service, repository):
        repository.find_all_for_matching.return_value = [make_wine(disponibile=False)]

        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("pasta al pomodoro")

    @pytest.mark.asyncio
    async def test_returns_suggested_wines_with_motivazione(self, service, repository, mock_groq_client):
        candidati = [make_wine(id="wine-1"), make_wine(id="wine-2", nome="Greco di Tufo")]
        repository.find_all_for_matching.return_value = candidati
        risposta = json.dumps({
            "suggerimenti": [
                {"wine_id": "wine-1", "motivazione": "Si abbina bene"},
                {"wine_id": "wine-2", "motivazione": "Alternativa valida"},
            ]
        })
        mock_groq_client.chat.completions.create.return_value = make_groq_response(risposta)

        risultati = await service.suggerisci_vini("pasta al pomodoro", limit=3)

        assert [wine.id for wine, _ in risultati] == ["wine-1", "wine-2"]
        assert risultati[0][1] == "Si abbina bene"

    @pytest.mark.asyncio
    async def test_respects_limit(self, service, repository, mock_groq_client):
        candidati = [make_wine(id=f"wine-{i}") for i in range(5)]
        repository.find_all_for_matching.return_value = candidati
        risposta = json.dumps({
            "suggerimenti": [{"wine_id": f"wine-{i}", "motivazione": "ok"} for i in range(5)]
        })
        mock_groq_client.chat.completions.create.return_value = make_groq_response(risposta)

        risultati = await service.suggerisci_vini("pasta", limit=2)

        assert len(risultati) == 2

    @pytest.mark.asyncio
    async def test_filters_out_hallucinated_wine_ids(self, service, repository, mock_groq_client):
        repository.find_all_for_matching.return_value = [make_wine(id="wine-1")]
        risposta = json.dumps({
            "suggerimenti": [
                {"wine_id": "wine-1", "motivazione": "ok"},
                {"wine_id": "wine-non-esistente", "motivazione": "allucinazione"},
                {"wine_id": 123, "motivazione": "id malformato"},
            ]
        })
        mock_groq_client.chat.completions.create.return_value = make_groq_response(risposta)

        risultati = await service.suggerisci_vini("pasta")

        assert len(risultati) == 1
        assert risultati[0][0].id == "wine-1"

    @pytest.mark.asyncio
    async def test_raises_when_all_suggestions_are_hallucinated(self, service, repository, mock_groq_client):
        repository.find_all_for_matching.return_value = [make_wine(id="wine-1")]
        risposta = json.dumps({"suggerimenti": [{"wine_id": "wine-fantasma", "motivazione": "no"}]})
        mock_groq_client.chat.completions.create.return_value = make_groq_response(risposta)

        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("pasta")

    @pytest.mark.asyncio
    async def test_raises_on_malformed_json(self, service, repository, mock_groq_client):
        repository.find_all_for_matching.return_value = [make_wine()]
        mock_groq_client.chat.completions.create.return_value = make_groq_response("non è json")

        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("pasta")

    @pytest.mark.asyncio
    async def test_raises_on_missing_suggerimenti_key(self, service, repository, mock_groq_client):
        repository.find_all_for_matching.return_value = [make_wine()]
        mock_groq_client.chat.completions.create.return_value = make_groq_response(json.dumps({}))

        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("pasta")

    @pytest.mark.asyncio
    async def test_raises_on_empty_groq_content(self, service, repository, mock_groq_client):
        repository.find_all_for_matching.return_value = [make_wine()]
        mock_groq_client.chat.completions.create.return_value = make_groq_response("")

        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("pasta")

    @pytest.mark.asyncio
    async def test_wraps_groq_api_error(self, service, repository, mock_groq_client):
        repository.find_all_for_matching.return_value = [make_wine()]
        mock_groq_client.chat.completions.create.side_effect = GroqAPIError(
            "boom", request=MagicMock(), body=None
        )

        with pytest.raises(PairingServiceError):
            await service.suggerisci_vini("pasta")
