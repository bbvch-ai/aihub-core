"""
Tests for image_processor focused on the dedup behavior added to
extract_and_upload_images. See image_processor.py for the rationale behind the
chosen hash function (dHash, hash_size=8) and the threshold (12 bits).
"""

import base64
import hashlib
import re
import struct
from io import BytesIO

import imagehash
import pytest
from PIL import Image, ImageDraw

from swiss_ai_hub.core.generative_ai.utils.image_processor import (
    _HASH_MATCH_THRESHOLD,
    _detect_extension,
    _find_perceptual_match,
    _image_hash,
    embed_images_as_base64,
    extract_and_upload_images,
    image_marker,
)


class _FakeFileSystem:
    """
    Minimal fsspec-compatible stub. Records every successful write so tests can
    assert on the exact set of S3 keys produced. Avoids depending on
    fsspec.implementations.memory internals.
    """

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.makedirs_calls: list[str] = []

    def makedirs(self, path: str, exist_ok: bool = False) -> None:
        self.makedirs_calls.append(path)

    def open(self, path: str, mode: str) -> "_FakeWriter":
        if mode != "wb":
            raise AssertionError(f"Unexpected open mode {mode!r} — production code only writes binary")
        return _FakeWriter(self, path)


class _FakeWriter:
    def __init__(self, fs: _FakeFileSystem, path: str) -> None:
        self._fs = fs
        self._path = path
        self._buf = BytesIO()

    def __enter__(self) -> BytesIO:
        return self._buf

    def __exit__(self, *_: object) -> None:
        self._fs.files[self._path] = self._buf.getvalue()


def _jpeg_bytes(img: Image.Image) -> bytes:
    out = BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=85)
    return out.getvalue()


def _png_bytes(img: Image.Image) -> bytes:
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _b64(img: Image.Image) -> str:
    """Mimic MinerU output: JPEG bytes wrapped in a data URI."""
    return f"data:image/jpeg;base64,{base64.b64encode(_jpeg_bytes(img)).decode()}"


def _make_logo(dx: int = 0, dy: int = 0, scale: float = 1.0) -> Image.Image:
    """
    Render a synthetic logo onto a larger canvas, then crop a 200x80 window with
    the supplied offset and optional sub-pixel rescale. Mirrors the kind of
    bounding-box jitter a VLM produces when re-detecting the same logo on
    different pages of a PDF.
    """
    canvas = Image.new("RGB", (260, 130), "white")
    d = ImageDraw.Draw(canvas)
    d.rectangle([30, 25, 230, 105], fill=(20, 60, 200))
    d.text((60, 50), "ACME CORP", fill="white")
    d.ellipse([180, 35, 220, 95], outline="yellow", width=3)

    x, y = 30 + dx, 25 + dy
    cropped = canvas.crop((x, y, x + 200, y + 80))
    if scale != 1.0:
        scaled = cropped.resize((int(200 * scale), int(80 * scale)), Image.LANCZOS)
        cropped = scaled.resize((200, 80), Image.LANCZOS)
    return cropped


def _make_distinct_figure(kind: str) -> Image.Image:
    img = Image.new("RGB", (400, 300), "white")
    d = ImageDraw.Draw(img)
    if kind == "lines":
        d.line([(0, 0), (400, 300), (0, 300), (400, 0)], fill="red", width=5)
    elif kind == "circle":
        d.ellipse([50, 50, 350, 250], outline="green", width=8)
    elif kind == "triangle":
        d.polygon([(200, 50), (50, 250), (350, 250)], fill="blue")
    else:
        raise ValueError(kind)
    return img


class TestPerceptualHash:
    def test_identical_bytes_produce_identical_hash(self) -> None:
        img_bytes = _jpeg_bytes(_make_logo())
        assert _image_hash(img_bytes) == _image_hash(img_bytes)

    def test_distinct_figures_produce_different_hashes(self) -> None:
        h_lines = _image_hash(_jpeg_bytes(_make_distinct_figure("lines")))
        h_circle = _image_hash(_jpeg_bytes(_make_distinct_figure("circle")))
        assert h_lines != h_circle

    def test_crop_jitter_stays_within_threshold(self) -> None:
        """The whole point of dHash: small crop offsets must yield small Hamming distances."""
        ref = _image_hash(_jpeg_bytes(_make_logo(0, 0, 1.0)))
        for dx, dy, scale in [(1, 0, 1.0), (-1, 0, 1.0), (0, 2, 1.0), (3, -1, 1.0), (0, 0, 0.97)]:
            jittered = _image_hash(_jpeg_bytes(_make_logo(dx, dy, scale)))
            assert ref - jittered <= _HASH_MATCH_THRESHOLD, (
                f"crop variation (dx={dx}, dy={dy}, scale={scale}) exceeded threshold "
                f"({ref - jittered} > {_HASH_MATCH_THRESHOLD})"
            )

    def test_distinct_figures_exceed_threshold(self) -> None:
        """Threshold must not collapse genuinely different content."""
        h_lines = _image_hash(_jpeg_bytes(_make_distinct_figure("lines")))
        h_circle = _image_hash(_jpeg_bytes(_make_distinct_figure("circle")))
        h_tri = _image_hash(_jpeg_bytes(_make_distinct_figure("triangle")))
        assert h_lines - h_circle > _HASH_MATCH_THRESHOLD
        assert h_lines - h_tri > _HASH_MATCH_THRESHOLD
        assert h_circle - h_tri > _HASH_MATCH_THRESHOLD


class TestFindPerceptualMatch:
    def test_empty_seen_returns_none(self) -> None:
        h = imagehash.hex_to_hash("0000000000000000")
        assert _find_perceptual_match(h, []) is None

    def test_exact_match_returns_uri(self) -> None:
        h = imagehash.hex_to_hash("abcd1234abcd1234")
        assert _find_perceptual_match(h, [(h, "s3://bucket/figure_1.jpg")]) == "s3://bucket/figure_1.jpg"

    def test_within_threshold_returns_uri(self) -> None:
        zero = imagehash.hex_to_hash("0000000000000000")
        # 12 bits set → Hamming distance exactly equal to the threshold (12).
        within = imagehash.hex_to_hash("0000000000000fff")
        assert _find_perceptual_match(within, [(zero, "s3://bucket/figure_1.jpg")]) == "s3://bucket/figure_1.jpg"

    def test_beyond_threshold_returns_none(self) -> None:
        zero = imagehash.hex_to_hash("0000000000000000")
        # 13 bits set → Hamming distance one above the threshold.
        beyond = imagehash.hex_to_hash("0000000000001fff")
        assert _find_perceptual_match(beyond, [(zero, "s3://bucket/figure_1.jpg")]) is None

    def test_returns_first_matching_uri(self) -> None:
        """When several stored hashes match, the earliest-inserted one wins (insertion-order semantics)."""
        zero = imagehash.hex_to_hash("0000000000000000")
        seen = [
            (zero, "s3://bucket/first.jpg"),
            (zero, "s3://bucket/second.jpg"),
        ]
        assert _find_perceptual_match(zero, seen) == "s3://bucket/first.jpg"


class TestDetectExtension:
    def test_data_uri_jpeg_returns_jpg(self) -> None:
        assert _detect_extension("data:image/jpeg;base64", "anything", b"") == "jpg"

    def test_data_uri_png_returns_png(self) -> None:
        assert _detect_extension("data:image/png;base64", "anything", b"") == "png"

    def test_falls_back_to_filename_extension(self) -> None:
        assert _detect_extension("", "logo.webp", b"") == "webp"

    def test_falls_back_to_pil_sniffing(self) -> None:
        jpeg = _jpeg_bytes(_make_distinct_figure("lines"))
        # No data URI prefix, no extension on the source name — must sniff JPEG via PIL.
        assert _detect_extension("", "no_extension", jpeg) == "jpg"


class TestExtractAndUploadImages:
    @pytest.mark.asyncio
    async def test_returns_markdown_unchanged_when_images_empty(self) -> None:
        fs = _FakeFileSystem()
        original = "# Hello\n\nNo figures here."
        result = await extract_and_upload_images(original, {}, fs, "bucket/docs/report.pdf")
        assert result == original
        assert fs.files == {}

    @pytest.mark.asyncio
    async def test_writes_one_file_per_unique_image(self) -> None:
        images = {
            "fig_a.jpg": _b64(_make_distinct_figure("lines")),
            "fig_b.jpg": _b64(_make_distinct_figure("circle")),
            "fig_c.jpg": _b64(_make_distinct_figure("triangle")),
        }
        md = "".join(f"![](images/{k})\n" for k in images)

        fs = _FakeFileSystem()
        await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        figure_files = [p for p in fs.files if "__figures__" in p]
        assert len(figure_files) == 3

    @pytest.mark.asyncio
    async def test_300_identical_logos_collapse_to_one_file(self) -> None:
        """The headline scenario: a 300-page PDF with the same logo on every page must store the logo once."""
        logo_b64 = _b64(_make_logo())
        images = {f"logo_p{i}.jpg": logo_b64 for i in range(300)}
        for kind in ("lines", "circle", "triangle"):
            images[f"fig_{kind}.jpg"] = _b64(_make_distinct_figure(kind))

        md = "".join(f"![](images/{k})\n" for k in images)

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        figure_files = [p for p in fs.files if "__figures__" in p]
        assert len(figure_files) == 4, f"expected 4 (1 deduped logo + 3 figures), got {len(figure_files)}"

        s3_uris_in_markdown = set(re.findall(r"s3://[^)]+", result))
        assert len(s3_uris_in_markdown) == 4

    @pytest.mark.asyncio
    async def test_logo_crop_variants_collapse_to_one_file(self) -> None:
        """VLM crop bounds drift between pages — re-cropped logos must still dedup."""
        crop_variations = [(0, 0, 1.0), (1, 0, 1.0), (-1, 0, 1.0), (0, 2, 1.0), (3, -1, 1.0), (0, 0, 0.97)]
        images = {f"logo_p{i}.jpg": _b64(_make_logo(*v)) for i, v in enumerate(crop_variations)}
        for kind in ("lines", "circle"):
            images[f"fig_{kind}.jpg"] = _b64(_make_distinct_figure(kind))

        md = "".join(f"![](images/{k})\n" for k in images)

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        figure_files = [p for p in fs.files if "__figures__" in p]
        assert len(figure_files) == 3, (
            f"expected 3 (1 deduped logo across all crop variants + 2 distinct figures), got {len(figure_files)}: "
            f"{figure_files}"
        )

        # The full markdown must reference exactly 3 distinct S3 URIs: one for the canonical logo
        # that all 6 crop variants collapsed onto, and one each for the two distinct figures.
        unique_uris = set(re.findall(r"s3://[^)]+", result))
        assert len(unique_uris) == 3, f"expected 3 unique S3 URIs in markdown, got {unique_uris}"

        # And the markdown must contain 8 figure tags total (6 logo refs + 2 figure refs), proving
        # the dedup hit path still rewrites the markdown rather than dropping refs.
        assert result.count("<figure>") == len(images)

    @pytest.mark.asyncio
    async def test_distinct_figures_remain_distinct(self) -> None:
        images = {
            "a.jpg": _b64(_make_distinct_figure("lines")),
            "b.jpg": _b64(_make_distinct_figure("circle")),
            "c.jpg": _b64(_make_distinct_figure("triangle")),
        }
        md = "".join(f"![](images/{k})\n" for k in images)

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        unique_uris = set(re.findall(r"s3://[^)]+", result))
        assert len(unique_uris) == 3

    @pytest.mark.asyncio
    async def test_filename_uses_content_hash_and_input_extension(self) -> None:
        """Output filename = figure_<sha256[:16]>.<detected_ext> — content-addressed and idempotent."""
        figure = _make_distinct_figure("lines")
        figure_b64 = _b64(figure)
        expected_bytes = base64.b64decode(figure_b64.split(",", 1)[1])
        expected_hash = hashlib.sha256(expected_bytes).hexdigest()[:16]

        fs = _FakeFileSystem()
        await extract_and_upload_images("![](images/a.jpg)", {"a.jpg": figure_b64}, fs, "bucket/docs/report.pdf")

        figure_files = [p for p in fs.files if "__figures__" in p]
        assert len(figure_files) == 1
        assert figure_files[0].endswith(f"figure_{expected_hash}.jpg")

    @pytest.mark.asyncio
    async def test_uploaded_bytes_are_unchanged(self) -> None:
        """We trust MinerU's JPEG output and never re-encode — bytes must round-trip verbatim."""
        figure_b64 = _b64(_make_distinct_figure("circle"))
        expected_bytes = base64.b64decode(figure_b64.split(",", 1)[1])

        fs = _FakeFileSystem()
        await extract_and_upload_images("![](images/a.jpg)", {"a.jpg": figure_b64}, fs, "bucket/docs/report.pdf")

        [stored_path] = [p for p in fs.files if "__figures__" in p]
        assert fs.files[stored_path] == expected_bytes

    @pytest.mark.asyncio
    async def test_png_input_keeps_png_extension(self) -> None:
        """If a loader ever feeds us PNG (MarkItDown tabular extraction, etc.), preserve the format."""
        png_b64 = base64.b64encode(_png_bytes(_make_distinct_figure("lines"))).decode()
        images = {"a.png": f"data:image/png;base64,{png_b64}"}

        fs = _FakeFileSystem()
        await extract_and_upload_images("![](images/a.png)", images, fs, "bucket/docs/report.pdf")

        [path] = [p for p in fs.files if "__figures__" in p]
        assert path.endswith(".png")
        with Image.open(BytesIO(fs.files[path])) as img:
            assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_handles_raw_base64_without_data_uri_prefix(self) -> None:
        """Some callers pass raw base64; we sniff the format from filename or PIL."""
        raw_b64 = base64.b64encode(_jpeg_bytes(_make_distinct_figure("lines"))).decode()
        images = {"a.jpg": raw_b64}

        fs = _FakeFileSystem()
        await extract_and_upload_images("![](images/a.jpg)", images, fs, "bucket/docs/report.pdf")

        [path] = [p for p in fs.files if "__figures__" in p]
        assert path.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_markdown_wraps_references_in_figure_tags(self) -> None:
        images = {"a.jpg": _b64(_make_distinct_figure("lines"))}
        md = "Before ![](images/a.jpg) after."

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        assert "<figure>" in result
        assert "</figure>" in result
        assert "images/a.jpg" not in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "ref_pattern",
        ["images/a.jpg", "./images/a.jpg", "a.jpg"],
    )
    async def test_rewrites_all_known_reference_styles(self, ref_pattern: str) -> None:
        images = {"a.jpg": _b64(_make_distinct_figure("lines"))}
        md = f"![alt]({ref_pattern})"

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        assert ref_pattern not in result
        assert "s3://" in result


SVG_URI = "data:image/svg+xml;base64," + base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"/>').decode()
SIGNATURE_ONLY_PNG_URI = "data:image/png;base64,iVBORw0KGgo="
IMAGE_HASH = "swiss_ai_hub.core.generative_ai.utils.image_processor._image_hash"


def _data_uri(mime: str, payload: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(payload).decode()}"


def _png_uri(img: Image.Image) -> str:
    return _data_uri("image/png", _png_bytes(img))


def _wmf(inch: int) -> bytes:
    """A placeable WMF header; Pillow raises OSError for inch=1440 and ValueError for inch=0."""
    head = struct.pack("<IHhhhhHIH", 0x9AC6CDD7, 0, 0, 0, 1440, 1440, inch, 0, 0)
    return head + struct.pack("<HHIHIH", 1, 9, 0x300, 0, 0, 0) + b"\x03\x00\x00\x00\x00\x00"


def _emf_with_zero_frame() -> bytes:
    """An EMF header Pillow answers with ZeroDivisionError, not OSError."""
    bounds = struct.pack("<iiii", 0, 0, 99, 99)
    frame = struct.pack("<iiii", 0, 0, 0, 0)
    tail = struct.pack("<IIIHHIIIiiii", 0x10000, 108, 1, 1, 0, 0, 0, 0, 1920, 1080, 508, 286)
    return struct.pack("<II", 1, 108) + bounds + frame + b" EMF" + tail


@pytest.fixture
def no_decoding(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(image_bytes: bytes) -> None:
        raise AssertionError("the MIME type must decide, without decoding the image")

    monkeypatch.setattr(IMAGE_HASH, fail)


class TestImageMarker:
    def test_keeps_the_alt_text(self) -> None:
        assert image_marker("  company logo ") == "[image: company logo]"

    def test_without_alt_text(self) -> None:
        assert image_marker(" ") == "[image]"


class TestSkippedImages:
    @pytest.mark.asyncio
    async def test_an_svg_between_two_figures_is_replaced_and_the_figures_stay_numbered(self) -> None:
        images = {
            "a.png": _png_uri(_make_distinct_figure("lines")),
            "logo.svg": SVG_URI,
            "b.png": _png_uri(_make_distinct_figure("circle")),
        }
        md = "![](a.png) ![logo](logo.svg) ![](b.png)"

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/deck.pptx")

        assert len(fs.files) == 2
        assert "[image: logo]" in result
        assert "![Figure 1](" in result
        assert "![Figure 2](" in result
        assert "Figure 3" not in result
        assert not any(path.endswith(".svg") for path in fs.files)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "data_uri",
        [
            _data_uri("image/x-wmf", _wmf(1440)),
            _data_uri("image/x-wmf", _wmf(0)),
            _data_uri("image/x-emf", _emf_with_zero_frame()),
        ],
        ids=["wmf", "wmf-inch-0", "emf-zero-frame"],
    )
    async def test_a_metafile_is_skipped_before_pillow_reads_it(self, data_uri: str, no_decoding: None) -> None:
        fs = _FakeFileSystem()
        result = await extract_and_upload_images("![clipart](x.wmf)", {"x.wmf": data_uri}, fs, "bucket/docs/a.docx")

        assert result == "[image: clipart]"
        assert fs.files == {}

    @pytest.mark.asyncio
    async def test_a_truncated_png_is_skipped_and_the_other_images_are_uploaded(self) -> None:
        truncated = _png_bytes(_make_distinct_figure("lines"))[:40]
        images = {
            "broken.png": _data_uri("image/png", truncated),
            "ok.png": _png_uri(_make_distinct_figure("circle")),
        }

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(
            "![chart](broken.png) ![](ok.png)", images, fs, "bucket/docs/report.pdf"
        )

        assert result.startswith("[image: chart] <figure>![Figure 1](s3://")
        assert len(fs.files) == 1

    @pytest.mark.asyncio
    async def test_raw_base64_that_does_not_decode_is_skipped(self) -> None:
        images = {"x.jpg": base64.b64encode(b"not an image at all").decode()}

        fs = _FakeFileSystem()
        result = await extract_and_upload_images("![scan](images/x.jpg)", images, fs, "bucket/docs/report.pdf")

        assert result == "[image: scan]"
        assert fs.files == {}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("reference", ["images/x.wmf", "./images/x.wmf", "x.wmf"])
    async def test_every_reference_style_keeps_its_alt_text(self, reference: str) -> None:
        images = {"x.wmf": _data_uri("image/x-wmf", _wmf(1440))}

        result = await extract_and_upload_images(f"![chart]({reference})", images, _FakeFileSystem(), "b/doc.pdf")

        assert result == "[image: chart]"

    @pytest.mark.asyncio
    async def test_dedup_still_works_across_a_skipped_image(self) -> None:
        images = {
            "logo_1.jpg": _b64(_make_logo()),
            "vector.svg": SVG_URI,
            "logo_2.jpg": _b64(_make_logo(1, 0)),
        }
        md = "![](logo_1.jpg) ![](vector.svg) ![](logo_2.jpg)"

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        assert len(fs.files) == 1
        assert len(set(re.findall(r"s3://[^)]+", result))) == 1
        assert "[image]" in result

    @pytest.mark.asyncio
    async def test_nothing_is_written_when_every_image_is_skipped(self) -> None:
        fs = _FakeFileSystem()
        result = await extract_and_upload_images("![logo](logo.svg)", {"logo.svg": SVG_URI}, fs, "bucket/docs/a.pptx")

        assert result == "[image: logo]"
        assert fs.files == {}
        assert fs.makedirs_calls == []

    @pytest.mark.asyncio
    async def test_a_decompression_bomb_still_fails_the_document(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def bomb(image_bytes: bytes) -> None:
            raise Image.DecompressionBombError("too many pixels")

        monkeypatch.setattr(IMAGE_HASH, bomb)
        images = {"a.png": _png_uri(_make_logo())}
        fs = _FakeFileSystem()

        with pytest.raises(Image.DecompressionBombError):
            await extract_and_upload_images("![](a.png)", images, fs, "bucket/docs/report.pdf")


class TestEmbedImagesAsBase64:
    def test_an_svg_is_replaced_and_a_png_is_embedded_without_decoding(self, no_decoding: None) -> None:
        images = {"logo.svg": SVG_URI, "chart.png": SIGNATURE_ONLY_PNG_URI}

        result = embed_images_as_base64("![logo](logo.svg) ![](chart.png)", images, source_file="deck.pptx")

        assert result == f"[image: logo] <figure>![Figure 1]({SIGNATURE_ONLY_PNG_URI})</figure>"

    def test_the_source_file_is_optional(self) -> None:
        assert embed_images_as_base64("![](logo.svg)", {"logo.svg": SVG_URI}) == "[image]"
