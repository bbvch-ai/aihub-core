import io
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException
from PIL import Image

from swiss_ai_hub.api.routes.file.figure_image import FigureImage


def _stored(image_format: str, mode: str = "RGB", size: tuple[int, int] = (40, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, size, color=(10, 20, 30, 128) if mode == "RGBA" else (10, 20, 30)).save(buffer, format=image_format)
    return buffer.getvalue()


def test_should_re_encode_an_opaque_figure_as_jpeg() -> None:
    figure = FigureImage.from_stored(_stored("PNG"))

    assert figure.media_type == "image/jpeg"
    assert Image.open(io.BytesIO(figure.content)).format == "JPEG"


def test_should_keep_transparency_as_png() -> None:
    figure = FigureImage.from_stored(_stored("PNG", mode="RGBA"))

    assert figure.media_type == "image/png"


def test_should_shrink_a_large_figure_to_the_maximum_side() -> None:
    figure = FigureImage.from_stored(_stored("JPEG", size=(5000, 1000)))

    assert max(Image.open(io.BytesIO(figure.content)).size) == FigureImage.MAX_SIDE


@pytest.mark.parametrize(
    "stored",
    [
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b"<html><script>alert(1)</script></html>",
        b"%PDF-1.7 not an image",
    ],
)
def test_should_refuse_anything_that_is_not_a_raster_image(stored: bytes) -> None:
    with pytest.raises(HTTPException) as error:
        FigureImage.from_stored(stored)

    assert error.value.status_code == 415


def test_should_refuse_a_figure_with_too_many_pixels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(FigureImage, "MAX_PIXELS", 100)

    with pytest.raises(HTTPException) as error:
        FigureImage.from_stored(_stored("PNG", size=(20, 20)))

    assert error.value.status_code == 415


def test_should_serve_with_headers_that_forbid_sniffing_and_scripts() -> None:
    response = FigureImage.from_stored(_stored("PNG")).to_response()

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"] == "default-src 'none'; sandbox"
    assert response.headers["content-type"] == "image/jpeg"


def _storage(head: Exception | int) -> MagicMock:
    s3_service = MagicMock()
    if isinstance(head, Exception):
        s3_service.file_size.side_effect = head
    else:
        s3_service.file_size.return_value = head
        s3_service.download_file.return_value = _stored("PNG")
    return s3_service


@pytest.mark.asyncio
@pytest.mark.parametrize("code", ["404", "NoSuchKey"])
async def test_should_answer_404_for_a_figure_whose_document_was_removed(code: str) -> None:
    missing = ClientError({"Error": {"Code": code}}, "HeadObject")

    with pytest.raises(HTTPException) as error:
        await FigureImage.from_storage(_storage(missing), "bucket", "a/__figures__/doc/figure.png")

    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_should_not_download_a_figure_larger_than_the_limit() -> None:
    s3_service = _storage(FigureImage.MAX_STORED_BYTES + 1)

    with pytest.raises(HTTPException) as error:
        await FigureImage.from_storage(s3_service, "bucket", "a/__figures__/doc/figure.png")

    assert error.value.status_code == 415
    s3_service.download_file.assert_not_called()


@pytest.mark.asyncio
async def test_should_let_other_storage_errors_through() -> None:
    denied = ClientError({"Error": {"Code": "AccessDenied"}}, "HeadObject")

    with pytest.raises(ClientError):
        await FigureImage.from_storage(_storage(denied), "bucket", "a/__figures__/doc/figure.png")
