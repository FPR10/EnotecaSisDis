"""
Unit test per app.config.security (validazione token Azure Entra e dependency FastAPI).

httpx (JWKS), jose.jwt e AuthenticationService vengono mockati: i test non fanno
alcuna chiamata di rete e non richiedono credenziali Azure reali.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError

from app.config import security
from app.entity.user_entity import User, UserRole


def make_settings(
    tenant_id="tenant-123",
    client_id="client-456",
    admin_role="Enoteca.Admin",
):
    return SimpleNamespace(
        azure_entra_tenant_id=tenant_id,
        azure_entra_client_id=client_id,
        azure_entra_admin_role=admin_role,
    )


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


class FakeJwksResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Il modulo mantiene una cache JWKS globale: va azzerata tra un test e l'altro."""
    security._jwks_cache = {}
    security._jwks_fetched_at = 0.0
    yield
    security._jwks_cache = {}
    security._jwks_fetched_at = 0.0


@pytest.fixture
def mock_settings():
    settings = make_settings()
    with patch.object(security, "settings", settings):
        yield settings


@pytest.fixture
def mock_httpx_get():
    """Mocka httpx.AsyncClient().get(...) usato per scaricare le JWKS."""
    response = FakeJwksResponse({"keys": [{"kid": "key-1", "kty": "RSA"}]})
    client_instance = MagicMock()
    client_instance.get = AsyncMock(return_value=response)
    client_instance.__aenter__ = AsyncMock(return_value=client_instance)
    client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("app.config.security.httpx.AsyncClient", return_value=client_instance) as client_class:
        yield client_class, client_instance


class TestGetJwks:
    @pytest.mark.asyncio
    async def test_fetches_jwks_when_cache_empty(self, mock_settings, mock_httpx_get):
        client_class, client_instance = mock_httpx_get

        jwks = await security._get_jwks()

        assert jwks == {"keys": [{"kid": "key-1", "kty": "RSA"}]}
        client_instance.get.assert_awaited_once()
        url_chiamato = client_instance.get.call_args.args[0]
        assert mock_settings.azure_entra_tenant_id in url_chiamato

    @pytest.mark.asyncio
    async def test_uses_cache_within_ttl(self, mock_settings, mock_httpx_get):
        _, client_instance = mock_httpx_get

        await security._get_jwks()
        await security._get_jwks()

        client_instance.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_refetches_after_ttl_expires(self, mock_settings, mock_httpx_get):
        _, client_instance = mock_httpx_get

        await security._get_jwks()
        security._jwks_fetched_at -= security._JWKS_TTL + 1
        await security._get_jwks()

        assert client_instance.get.await_count == 2


class TestValidateAzureToken:
    @pytest.mark.asyncio
    async def test_raises_when_token_malformed(self, mock_settings):
        with patch("app.config.security.jwt.get_unverified_header", side_effect=JWTError("bad")):
            with pytest.raises(HTTPException) as exc_info:
                await security._validate_azure_token("token-malformato")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_when_key_not_found(self, mock_settings, mock_httpx_get):
        with patch("app.config.security.jwt.get_unverified_header", return_value={"kid": "key-assente"}):
            with pytest.raises(HTTPException) as exc_info:
                await security._validate_azure_token("token")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_when_decode_fails(self, mock_settings, mock_httpx_get):
        with patch("app.config.security.jwt.get_unverified_header", return_value={"kid": "key-1"}), \
             patch("app.config.security.jwt.decode", side_effect=JWTError("firma non valida")):
            with pytest.raises(HTTPException) as exc_info:
                await security._validate_azure_token("token")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_payload_on_success(self, mock_settings, mock_httpx_get):
        payload_atteso = {"oid": "oid-1", "email": "mario@example.com"}
        with patch("app.config.security.jwt.get_unverified_header", return_value={"kid": "key-1"}), \
             patch("app.config.security.jwt.decode", return_value=payload_atteso) as decode_mock:
            payload = await security._validate_azure_token("token")

        assert payload == payload_atteso
        assert decode_mock.call_args.kwargs["audience"] == mock_settings.azure_entra_client_id


class TestGetCurrentUser:
    @pytest.fixture
    def mock_validate_token(self):
        with patch("app.config.security._validate_azure_token", new_callable=AsyncMock) as fn:
            yield fn

    @pytest.fixture
    def mock_auth_service(self):
        with patch("app.config.security.AuthenticationService") as service_class:
            instance = MagicMock()
            instance.sincronizza_da_azure = AsyncMock()
            service_class.return_value = instance
            yield instance

    @pytest.mark.asyncio
    async def test_raises_when_authorization_header_missing(self, mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(authorization=None, db=MagicMock())

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_when_not_bearer_scheme(self, mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(authorization="Basic xxx", db=MagicMock())

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_when_oid_missing(self, mock_settings, mock_validate_token):
        mock_validate_token.return_value = {"email": "mario@example.com"}

        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(authorization="Bearer token", db=MagicMock())

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_assigns_admin_role_from_token_roles(self, mock_settings, mock_validate_token, mock_auth_service):
        mock_validate_token.return_value = {
            "oid": "oid-1",
            "email": "mario@example.com",
            "name": "Mario Rossi",
            "roles": [mock_settings.azure_entra_admin_role],
        }
        mock_auth_service.sincronizza_da_azure.return_value = make_user(ruolo=UserRole.ADMIN)

        await security.get_current_user(authorization="Bearer token", db=MagicMock())

        ruolo_passato = mock_auth_service.sincronizza_da_azure.call_args.kwargs["ruolo"]
        assert ruolo_passato == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_assigns_user_role_when_admin_role_absent(self, mock_settings, mock_validate_token, mock_auth_service):
        mock_validate_token.return_value = {
            "oid": "oid-1",
            "email": "mario@example.com",
            "roles": [],
        }
        mock_auth_service.sincronizza_da_azure.return_value = make_user(ruolo=UserRole.USER)

        await security.get_current_user(authorization="Bearer token", db=MagicMock())

        ruolo_passato = mock_auth_service.sincronizza_da_azure.call_args.kwargs["ruolo"]
        assert ruolo_passato == UserRole.USER

    @pytest.mark.asyncio
    async def test_raises_when_account_disabled(self, mock_settings, mock_validate_token, mock_auth_service):
        mock_validate_token.return_value = {"oid": "oid-1", "email": "mario@example.com", "roles": []}
        mock_auth_service.sincronizza_da_azure.return_value = make_user(is_active=False)

        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(authorization="Bearer token", db=MagicMock())

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_synced_user(self, mock_settings, mock_validate_token, mock_auth_service):
        utente_sincronizzato = make_user()
        mock_validate_token.return_value = {"oid": "oid-1", "email": "mario@example.com", "roles": []}
        mock_auth_service.sincronizza_da_azure.return_value = utente_sincronizzato

        utente = await security.get_current_user(authorization="Bearer token", db=MagicMock())

        assert utente is utente_sincronizzato


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_raises_when_not_admin(self):
        with pytest.raises(HTTPException) as exc_info:
            await security.require_admin(current_user=make_user(ruolo=UserRole.USER))

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_user_when_admin(self):
        admin = make_user(ruolo=UserRole.ADMIN)

        risultato = await security.require_admin(current_user=admin)

        assert risultato is admin
