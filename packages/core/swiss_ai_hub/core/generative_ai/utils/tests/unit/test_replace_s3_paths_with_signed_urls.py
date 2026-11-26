import base64
from io import BytesIO

import pytest
from fsspec.implementations.memory import MemoryFileSystem
from PIL import Image

from swiss_ai_hub.core.generative_ai.utils.image_processor import (
    extract_and_upload_images,
    replace_s3_paths_with_signed_urls,
)


class _RecordingSigner:
    """Signs a key the way a presigned URL looks, and records which keys it was asked for."""

    def __init__(self) -> None:
        self.signed: list[tuple[str, str]] = []

    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        self.signed.append((container, file_path))
        return f"https://s3.example/{container}/{file_path}?X-Amz-Signature=sig"


def _png_data_uri() -> str:
    out = BytesIO()
    Image.new("RGB", (32, 32), (200, 30, 30)).save(out, format="PNG")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()


async def _signed(markdown: str) -> tuple[str, _RecordingSigner]:
    signer = _RecordingSigner()
    result = await replace_s3_paths_with_signed_urls(markdown, s3_service=signer)  # type: ignore[arg-type]
    return result, signer


class TestReplaceS3PathsWithSignedUrls:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "key",
        [
            "api_uploads/__figures__/report_pdf/figure_0123456789abcdef.png",
            "api_uploads/__figures__/5cac_Jabra_Einstellungen_(1)_docx/figure_f05d7384c766b7af.png",
            "Office Equipment/__figures__/Preisliste_(Entwurf)_[v2]_xlsx/figure_63d64e2ab2f26d9c.jpg",
            "Ablage/__figures__/Bestellübersicht_März_pdf/figure_3452350d53a65ff4.webp",
        ],
    )
    async def test_the_whole_figure_key_is_signed(self, key: str) -> None:
        result, signer = await _signed(f"<figure>![Figure 1](s3://shared/{key})</figure>")

        assert signer.signed == [("shared", key)]
        assert result == f"<figure>![Figure 1](https://s3.example/shared/{key}?X-Amz-Signature=sig)</figure>"

    @pytest.mark.asyncio
    async def test_two_figures_on_one_line_are_signed_separately(self) -> None:
        first = "docs/__figures__/a_(1)_pdf/figure_00000000000000aa.png"
        second = "docs/__figures__/a_(1)_pdf/figure_00000000000000bb.png"

        _, signer = await _signed(f"![Figure 1](s3://b/{first}) and ![Figure 2](s3://b/{second}) (see above)")

        assert signer.signed == [("b", first), ("b", second)]

    @pytest.mark.asyncio
    async def test_text_in_parentheses_after_a_figure_is_kept(self) -> None:
        key = "docs/__figures__/a_pdf/figure_00000000000000aa.png"

        result, _ = await _signed(f"![Figure 1](s3://b/{key}) (Abbildung 1)")

        assert result == f"![Figure 1](https://s3.example/b/{key}?X-Amz-Signature=sig) (Abbildung 1)"

    @pytest.mark.asyncio
    async def test_a_chat_upload_named_with_a_parenthesis_gets_a_working_figure_url(self) -> None:
        fs = MemoryFileSystem()
        source = "shared/api_uploads/5cac_Jabra_Einstellungen_(1).docx"

        markdown = await extract_and_upload_images("![](image1.png)", {"image1.png": _png_data_uri()}, fs, source)
        result, signer = await _signed(markdown)

        [(container, key)] = signer.signed
        assert fs.exists(f"{container}/{key}")
        assert result.endswith("?X-Amz-Signature=sig)</figure>")
