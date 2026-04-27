"""
Tests for image_processor focused on the dedup + compression behavior added to
extract_and_upload_images. See image_processor.py for the rationale behind the
chosen hash function (dHash, hash_size=8) and the threshold (12 bits).
"""

import base64
import os
import re
from io import BytesIO

import imagehash
import pytest
from PIL import Image, ImageDraw

from swiss_ai_hub.core.generative_ai.utils.image_processor import (
    _HASH_MATCH_THRESHOLD,
    _compress_png,
    _find_perceptual_match,
    _perceptual_hash,
    extract_and_upload_images,
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


def _png_bytes(img: Image.Image) -> bytes:
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _b64(img: Image.Image) -> str:
    return base64.b64encode(_png_bytes(img)).decode()


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


def _random_photograph(size: int = 256) -> Image.Image:
    """RGB noise with > 50k unique colors — exercises the photograph branch of _compress_png."""
    return Image.frombytes("RGB", (size, size), os.urandom(size * size * 3))


class TestPerceptualHash:
    def test_identical_bytes_produce_identical_hash(self) -> None:
        img_bytes = _png_bytes(_make_logo())
        assert _perceptual_hash(img_bytes) == _perceptual_hash(img_bytes)

    def test_distinct_figures_produce_different_hashes(self) -> None:
        h_lines = _perceptual_hash(_png_bytes(_make_distinct_figure("lines")))
        h_circle = _perceptual_hash(_png_bytes(_make_distinct_figure("circle")))
        assert h_lines != h_circle

    def test_crop_jitter_stays_within_threshold(self) -> None:
        """The whole point of dHash: small crop offsets must yield small Hamming distances."""
        ref = _perceptual_hash(_png_bytes(_make_logo(0, 0, 1.0)))
        for dx, dy, scale in [(1, 0, 1.0), (-1, 0, 1.0), (0, 2, 1.0), (3, -1, 1.0), (0, 0, 0.97)]:
            jittered = _perceptual_hash(_png_bytes(_make_logo(dx, dy, scale)))
            assert ref - jittered <= _HASH_MATCH_THRESHOLD, (
                f"crop variation (dx={dx}, dy={dy}, scale={scale}) exceeded threshold "
                f"({ref - jittered} > {_HASH_MATCH_THRESHOLD})"
            )

    def test_distinct_figures_exceed_threshold(self) -> None:
        """Threshold must not collapse genuinely different content."""
        h_lines = _perceptual_hash(_png_bytes(_make_distinct_figure("lines")))
        h_circle = _perceptual_hash(_png_bytes(_make_distinct_figure("circle")))
        h_tri = _perceptual_hash(_png_bytes(_make_distinct_figure("triangle")))
        assert h_lines - h_circle > _HASH_MATCH_THRESHOLD
        assert h_lines - h_tri > _HASH_MATCH_THRESHOLD
        assert h_circle - h_tri > _HASH_MATCH_THRESHOLD


class TestFindPerceptualMatch:
    def test_empty_seen_returns_none(self) -> None:
        h = imagehash.hex_to_hash("0000000000000000")
        assert _find_perceptual_match(h, []) is None

    def test_exact_match_returns_uri(self) -> None:
        h = imagehash.hex_to_hash("abcd1234abcd1234")
        assert _find_perceptual_match(h, [(h, "s3://bucket/figure_1.png")]) == "s3://bucket/figure_1.png"

    def test_within_threshold_returns_uri(self) -> None:
        zero = imagehash.hex_to_hash("0000000000000000")
        # 12 bits set → Hamming distance exactly equal to the threshold (12).
        within = imagehash.hex_to_hash("0000000000000fff")
        assert _find_perceptual_match(within, [(zero, "s3://bucket/figure_1.png")]) == "s3://bucket/figure_1.png"

    def test_beyond_threshold_returns_none(self) -> None:
        zero = imagehash.hex_to_hash("0000000000000000")
        # 13 bits set → Hamming distance one above the threshold.
        beyond = imagehash.hex_to_hash("0000000000001fff")
        assert _find_perceptual_match(beyond, [(zero, "s3://bucket/figure_1.png")]) is None

    def test_returns_first_matching_uri(self) -> None:
        """When several stored hashes match, the earliest-inserted one wins (insertion-order semantics)."""
        zero = imagehash.hex_to_hash("0000000000000000")
        seen = [
            (zero, "s3://bucket/first.png"),
            (zero, "s3://bucket/second.png"),
        ]
        assert _find_perceptual_match(zero, seen) == "s3://bucket/first.png"


class TestCompressPng:
    def test_output_is_valid_png(self) -> None:
        compressed = _compress_png(_png_bytes(_make_distinct_figure("lines")))
        with Image.open(BytesIO(compressed)) as img:
            assert img.format == "PNG"

    def test_output_preserves_dimensions(self) -> None:
        original = _make_distinct_figure("circle")
        compressed = _compress_png(_png_bytes(original))
        with Image.open(BytesIO(compressed)) as img:
            assert img.size == original.size

    def test_graphics_image_is_quantized(self) -> None:
        """Graphics with few colors must end up as paletted PNGs (mode 'P')."""
        compressed = _compress_png(_png_bytes(_make_distinct_figure("lines")))
        with Image.open(BytesIO(compressed)) as img:
            assert img.mode == "P", f"expected paletted PNG, got mode {img.mode}"

    def test_photograph_is_not_quantized(self) -> None:
        """High-color images (>50k unique colors) must keep truecolor depth — quantizing photos causes banding."""
        photo_bytes = _png_bytes(_random_photograph())
        compressed = _compress_png(photo_bytes)
        # The defensive fallback may return the original bytes unchanged for already-incompressible
        # noise. Either way, the result must not be a paletted image.
        with Image.open(BytesIO(compressed)) as img:
            assert img.mode in ("RGB", "RGBA"), f"photograph was quantized to mode {img.mode}"

    def test_graphics_compress_smaller(self) -> None:
        original_bytes = _png_bytes(_make_distinct_figure("lines"))
        compressed = _compress_png(original_bytes)
        assert len(compressed) <= len(original_bytes)

    def test_returns_original_when_compression_would_grow_file(self) -> None:
        """Defensive fallback: never replace input bytes with a larger 'compressed' result."""
        # An already-tiny PNG can't be compressed further. _compress_png must return the original.
        tiny = Image.new("RGB", (1, 1), "white")
        original_bytes = _png_bytes(tiny)
        compressed = _compress_png(original_bytes)
        assert len(compressed) <= len(original_bytes)

    def test_alpha_channel_preserved(self) -> None:
        """RGBA inputs must round-trip with alpha intact — Pillow's MEDIANCUT path can't dither alpha,
        so the production code skips quantization for alpha-bearing images and relies on optimize=True."""
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        compressed = _compress_png(_png_bytes(img))
        with Image.open(BytesIO(compressed)) as result:
            assert result.mode == "RGBA"
            # Sample a pixel to confirm alpha survived the round-trip.
            assert result.getpixel((25, 25))[3] == 128


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
            "fig_a.png": _b64(_make_distinct_figure("lines")),
            "fig_b.png": _b64(_make_distinct_figure("circle")),
            "fig_c.png": _b64(_make_distinct_figure("triangle")),
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
        images = {f"logo_p{i}.png": logo_b64 for i in range(300)}
        for kind in ("lines", "circle", "triangle"):
            images[f"fig_{kind}.png"] = _b64(_make_distinct_figure(kind))

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
        images = {f"logo_p{i}.png": _b64(_make_logo(*v)) for i, v in enumerate(crop_variations)}
        for kind in ("lines", "circle"):
            images[f"fig_{kind}.png"] = _b64(_make_distinct_figure(kind))

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
            "a.png": _b64(_make_distinct_figure("lines")),
            "b.png": _b64(_make_distinct_figure("circle")),
            "c.png": _b64(_make_distinct_figure("triangle")),
        }
        md = "".join(f"![](images/{k})\n" for k in images)

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        unique_uris = set(re.findall(r"s3://[^)]+", result))
        assert len(unique_uris) == 3

    @pytest.mark.asyncio
    async def test_output_files_are_png_extension(self) -> None:
        """Re-encoding always produces PNG; the source extension from MinerU is irrelevant."""
        images = {"weird_name.jpeg": _b64(_make_distinct_figure("lines"))}
        md = "![](images/weird_name.jpeg)"

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        figure_files = [p for p in fs.files if "__figures__" in p]
        assert len(figure_files) == 1
        assert figure_files[0].endswith(".png")
        assert ".png)" in result

    @pytest.mark.asyncio
    async def test_handles_data_uri_prefixed_base64(self) -> None:
        """MinerU sometimes returns 'data:image/png;base64,XYZ' — we strip the prefix."""
        raw_b64 = _b64(_make_distinct_figure("lines"))
        images = {"a.png": f"data:image/png;base64,{raw_b64}"}
        md = "![](images/a.png)"

        fs = _FakeFileSystem()
        await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        figure_files = [p for p in fs.files if "__figures__" in p]
        assert len(figure_files) == 1
        # And the file must be a valid PNG, proving we stripped the prefix correctly.
        with Image.open(BytesIO(fs.files[figure_files[0]])) as img:
            assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_markdown_wraps_references_in_figure_tags(self) -> None:
        images = {"a.png": _b64(_make_distinct_figure("lines"))}
        md = "Before ![](images/a.png) after."

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        assert "<figure>" in result
        assert "</figure>" in result
        assert "images/a.png" not in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "ref_pattern",
        ["images/a.png", "./images/a.png", "a.png"],
    )
    async def test_rewrites_all_known_reference_styles(self, ref_pattern: str) -> None:
        images = {"a.png": _b64(_make_distinct_figure("lines"))}
        md = f"![alt]({ref_pattern})"

        fs = _FakeFileSystem()
        result = await extract_and_upload_images(md, images, fs, "bucket/docs/report.pdf")

        assert ref_pattern not in result
        assert "s3://" in result
