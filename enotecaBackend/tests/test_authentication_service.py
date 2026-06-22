"""
Unit test per AuthenticationService.

Lo UserRepository viene mockato (AsyncMock): i test non toccano alcun
database reale.
"""

from unittest.mock import AsyncMock

import pytest

from app.entity.user_entity import User, UserRole
from app.service.authentication_service import AuthenticationService, AuthenticationServiceError


def make_user(**overrides) -> User:
    dati = dict(
        id="user-1",
        azure_oid="oid-1",
        email="mario@example.com",
        nome="Mario Rossi",
        ruolo=UserRole.USER,
        is_active=True,
    )
    dati.update(overrides)
    return User(**dati)


@pytest.fixture
def repository():
    return AsyncMock()


@pytest.fixture
def service(repository):
    return AuthenticationService(repository)


class TestSincronizzaDaAzure:
    @pytest.mark.asyncio
    async def test_raises_when_azure_oid_missing(self, service, repository):
        with pytest.raises(AuthenticationServiceError):
            await service.sincronizza_da_azure(
                azure_oid="", email="mario@example.com", nome="Mario", ruolo=UserRole.USER
            )

        repository.find_by_azure_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_user_on_first_login(self, service, repository):
        repository.find_by_azure_id.return_value = None
        repository.save.side_effect = lambda user: user

        utente = await service.sincronizza_da_azure(
            azure_oid="oid-nuovo", email="nuovo@example.com", nome="Nuovo Utente", ruolo=UserRole.USER
        )

        assert utente.azure_oid == "oid-nuovo"
        assert utente.email == "nuovo@example.com"
        repository.save.assert_awaited_once()
        repository.update_last_login.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_resyncs_existing_user_and_updates_last_login(self, service, repository):
        esistente = make_user(email="vecchia@example.com", ruolo=UserRole.USER)
        repository.find_by_azure_id.return_value = esistente

        utente = await service.sincronizza_da_azure(
            azure_oid="oid-1", email="nuova@example.com", nome="Nome Nuovo", ruolo=UserRole.ADMIN
        )

        assert utente.email == "nuova@example.com"
        assert utente.nome == "Nome Nuovo"
        assert utente.ruolo == UserRole.ADMIN
        repository.update_last_login.assert_awaited_once_with(esistente)
        repository.save.assert_not_awaited()


class TestGetUtente:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self, service, repository):
        repository.find_by_id.return_value = make_user()

        utente = await service.get_utente("user-1")

        assert utente.id == "user-1"

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, service, repository):
        repository.find_by_id.return_value = None

        with pytest.raises(AuthenticationServiceError):
            await service.get_utente("missing")


class TestGetUtenteByEmail:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self, service, repository):
        repository.find_by_email.return_value = make_user()

        utente = await service.get_utente_by_email("mario@example.com")

        assert utente is not None
        assert utente.email == "mario@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, service, repository):
        repository.find_by_email.return_value = None

        utente = await service.get_utente_by_email("assente@example.com")

        assert utente is None
