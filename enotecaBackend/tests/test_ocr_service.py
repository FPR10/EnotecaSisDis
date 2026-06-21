"""
Unit test per OcrService.

Il client Azure (ImageAnalysisClient) e get_settings vengono mockati:
i test non fanno alcuna chiamata di rete e non richiedono credenziali reali.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import HttpResponseError

from app.service.ocr_service import OcrService, OCRServiceError


def make_settings(endpoint="https://fake.cognitiveservices.azure.com/", key="fake-key"):
    return SimpleNamespace(azure_vision_endpoint=endpoint, azure_vision_key=key)


def make_read_result(lines_per_block):
    """Costruisce un risultato fittizio di Azure AI Vision (analyze().read)."""
    blocks = [
        SimpleNamespace(lines=[SimpleNamespace(text=text) for text in lines])
        for lines in lines_per_block
    ]
    return SimpleNamespace(read=SimpleNamespace(blocks=blocks))


@pytest.fixture
def mock_client_class():
    with patch("app.service.ocr_service.ImageAnalysisClient") as client_class:
        yield client_class


@pytest.fixture
def service(mock_client_class):
    with patch("app.service.ocr_service.get_settings", return_value=make_settings()):
        return OcrService()


class TestInit:
    def test_raises_when_endpoint_missing(self, mock_client_class):
        with patch(
            "app.service.ocr_service.get_settings",
            return_value=make_settings(endpoint=""),
        ):
            with pytest.raises(OCRServiceError):
                OcrService()

    def test_raises_when_key_missing(self, mock_client_class):
        with patch(
            "app.service.ocr_service.get_settings",
            return_value=make_settings(key=""),
        ):
            with pytest.raises(OCRServiceError):
                OcrService()

    def test_builds_client_with_settings(self, mock_client_class):
        settings = make_settings()
        with patch("app.service.ocr_service.get_settings", return_value=settings):
            OcrService()

        assert mock_client_class.call_args.kwargs["endpoint"] == settings.azure_vision_endpoint


class TestExtractText:
    @pytest.mark.asyncio
    async def test_raises_on_empty_image(self, service):
        with pytest.raises(OCRServiceError):
            await service.extract_text(b"")

        service._client.analyze.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_joined_lines(self, service):
        service._client.analyze.return_value = make_read_result(
            [["Chianti", "Riserva"], ["2019"]]
        )

        text = await service.extract_text(b"fake-bytes")

        assert text == "Chianti\nRiserva\n2019"

    @pytest.mark.asyncio
    async def test_returns_empty_string_when_no_read(self, service):
        service._client.analyze.return_value = SimpleNamespace(read=None)

        text = await service.extract_text(b"fake-bytes")

        assert text == ""

    @pytest.mark.asyncio
    async def test_wraps_http_response_error(self, service):
        service._client.analyze.side_effect = HttpResponseError("boom")

        with pytest.raises(OCRServiceError):
            await service.extract_text(b"fake-bytes")


class TestClose:
    def test_close_delegates_to_client(self, service):
        service.close()

        service._client.close.assert_called_once()
