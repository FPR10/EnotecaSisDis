"""
Unit test per BlobStorageService.

Il client Azure (BlobServiceClient) e get_settings vengono mockati: i test non
fanno alcuna chiamata di rete e non richiedono una connection string reale.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import HttpResponseError

from app.service.blob_storage_service import BlobStorageService, BlobStorageServiceError


def make_settings(
    connection_string="DefaultEndpointsProtocol=https;AccountName=fake;AccountKey=fake;",
    container_etichette="etichette",
    container_audit="import-audit",
):
    return SimpleNamespace(
        azure_storage_connection_string=connection_string,
        azure_storage_container_etichette=container_etichette,
        azure_storage_container_audit=container_audit,
    )


@pytest.fixture
def mock_blob_client():
    blob_client = MagicMock()
    blob_client.url = "https://fake.blob.core.windows.net/container/blob.jpg"
    return blob_client


@pytest.fixture
def mock_client_class(mock_blob_client):
    with patch("app.service.blob_storage_service.BlobServiceClient") as client_class:
        instance = MagicMock()
        instance.get_blob_client.return_value = mock_blob_client
        client_class.from_connection_string.return_value = instance
        yield client_class


@pytest.fixture
def service(mock_client_class):
    with patch("app.service.blob_storage_service.get_settings", return_value=make_settings()):
        return BlobStorageService()


class TestInit:
    def test_raises_when_connection_string_missing(self, mock_client_class):
        with patch(
            "app.service.blob_storage_service.get_settings",
            return_value=make_settings(connection_string=""),
        ):
            with pytest.raises(BlobStorageServiceError):
                BlobStorageService()

    def test_builds_client_from_connection_string(self, mock_client_class):
        settings = make_settings()
        with patch("app.service.blob_storage_service.get_settings", return_value=settings):
            BlobStorageService()

        mock_client_class.from_connection_string.assert_called_once_with(
            settings.azure_storage_connection_string
        )


class TestUploadEtichetta:
    @pytest.mark.asyncio
    async def test_uploads_to_etichette_container_and_returns_url(self, service, mock_blob_client):
        url = await service.upload_etichetta(b"fake-bytes", "wine-1", "foto.jpg")

        container_usato = service._client.get_blob_client.call_args.kwargs["container"]
        assert container_usato == "etichette"
        assert url == mock_blob_client.url
        mock_blob_client.upload_blob.assert_called_once()
        assert mock_blob_client.upload_blob.call_args.kwargs["overwrite"] is True

    @pytest.mark.asyncio
    async def test_blob_name_includes_wine_id(self, service):
        await service.upload_etichetta(b"fake-bytes", "wine-42", "foto.png")

        nome_blob = service._client.get_blob_client.call_args.kwargs["blob"]
        assert nome_blob.startswith("wine-42/")
        assert nome_blob.endswith(".png")

    @pytest.mark.asyncio
    async def test_defaults_to_jpg_when_no_extension(self, service):
        await service.upload_etichetta(b"fake-bytes", "wine-1", "foto_senza_estensione")

        nome_blob = service._client.get_blob_client.call_args.kwargs["blob"]
        assert nome_blob.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_content_type_matches_extension(self, service):
        await service.upload_etichetta(b"fake-bytes", "wine-1", "foto.png")

        content_settings = service._client.get_blob_client.return_value.upload_blob.call_args.kwargs[
            "content_settings"
        ]
        assert content_settings.content_type == "image/png"

    @pytest.mark.asyncio
    async def test_wraps_http_response_error(self, service, mock_blob_client):
        mock_blob_client.upload_blob.side_effect = HttpResponseError("boom")

        with pytest.raises(BlobStorageServiceError):
            await service.upload_etichetta(b"fake-bytes", "wine-1", "foto.jpg")


class TestUploadAuditImport:
    @pytest.mark.asyncio
    async def test_uploads_to_audit_container(self, service):
        await service.upload_audit_import(b"a,b,c", "vini.csv", "admin@enoteca.local")

        container_usato = service._client.get_blob_client.call_args.kwargs["container"]
        assert container_usato == "import-audit"

    @pytest.mark.asyncio
    async def test_blob_name_includes_filename_and_email(self, service):
        await service.upload_audit_import(b"a,b,c", "vini.csv", "admin@enoteca.local")

        nome_blob = service._client.get_blob_client.call_args.kwargs["blob"]
        assert "admin@enoteca.local" in nome_blob
        assert nome_blob.endswith("vini.csv")

    @pytest.mark.asyncio
    async def test_returns_blob_url(self, service, mock_blob_client):
        url = await service.upload_audit_import(b"a,b,c", "vini.csv", "admin@enoteca.local")

        assert url == mock_blob_client.url


class TestClose:
    def test_close_delegates_to_client(self, service):
        service.close()

        service._client.close.assert_called_once()
