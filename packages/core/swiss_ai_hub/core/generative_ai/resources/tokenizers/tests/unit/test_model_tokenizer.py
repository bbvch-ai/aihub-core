"""The vendored bge-m3 tokenizer has to count what the providers bill and enforce. The fixture holds the usage
Phoeniqs and stoney reported for the spike's 24 samples (prose in three languages, code, tables, numbers, emoji and
CJK, whitespace-heavy text), so a provider that changes its tokenizer fails here rather than in ingestion."""

import hashlib
import json
from pathlib import Path

import pytest

from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import (
    FALLBACK_TOKENIZER_ID,
    VENDORED_DIRECTORY,
    ModelTokenizer,
)

FIXTURE = json.loads((Path(__file__).parent / "bge_m3_provider_counts.json").read_text(encoding="utf-8"))
SAMPLES = FIXTURE["samples"]
EMBED_OVERHEAD = FIXTURE["embed_overhead_tokens"]
RERANK_OVERHEAD = FIXTURE["rerank_overhead_tokens"]
PROVIDER_USAGE_KEYS = ["phoeniqs_embed_usage", "stoney_embed_usage"]


@pytest.fixture(scope="module")
def bge_m3() -> ModelTokenizer:
    return ModelTokenizer.shared("bge-m3")


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample["id"] for sample in SAMPLES])
@pytest.mark.parametrize("usage_key", PROVIDER_USAGE_KEYS)
def test_embedding_count_never_undercounts_and_overcounts_by_at_most_one(
    bge_m3: ModelTokenizer, sample: dict, usage_key: str
) -> None:
    content_tokens = sample[usage_key] - EMBED_OVERHEAD

    assert content_tokens <= bge_m3.count(sample["text"]) <= content_tokens + 1


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample["id"] for sample in SAMPLES])
@pytest.mark.parametrize("usage_key", ["phoeniqs_rerank_usage", "stoney_rerank_usage"])
def test_rerank_pair_count_never_undercounts(bge_m3: ModelTokenizer, sample: dict, usage_key: str) -> None:
    """A pair is billed as query + document + 4 special tokens; both sides carry the +1 margin."""
    counted = bge_m3.count(FIXTURE["rerank_query"]) + bge_m3.count(sample["text"]) + RERANK_OVERHEAD

    assert sample[usage_key] <= counted <= sample[usage_key] + 2


@pytest.mark.parametrize(
    "edge", FIXTURE["trailing_whitespace"], ids=[repr(edge["text"]) for edge in FIXTURE["trailing_whitespace"]]
)
def test_trailing_whitespace_is_not_undercounted(bge_m3: ModelTokenizer, edge: dict) -> None:
    """sentencepiece drops what tokenizer.json keeps at the end of an input; the margin covers it."""
    assert edge["tokenizer_json_count"] <= bge_m3.count(edge["text"]) <= edge["tokenizer_json_count"] + 1


def test_encoding_carries_no_special_tokens(bge_m3: ModelTokenizer) -> None:
    """The splitter sums encodings of pieces; special tokens would shrink every piece by two."""
    assert len(bge_m3.encode_without_specials("Hallo")) == bge_m3.count("Hallo") - 1


def test_vendored_file_is_the_one_recorded_in_its_source() -> None:
    source = ModelTokenizer.vendored_source("bge-m3")
    model_file = ModelTokenizer.vendored_directory("bge-m3") / source["file"]

    assert hashlib.sha256(model_file.read_bytes()).hexdigest() == source["sha256"]
    assert source["tokenizer_id"] == "bge-m3"
    assert len(source["revision"]) == 40


@pytest.mark.parametrize("directory", sorted(path for path in VENDORED_DIRECTORY.iterdir() if path.is_dir()))
def test_every_vendored_tokenizer_has_its_licence_and_source(directory: Path) -> None:
    assert (directory / "LICENSE").is_file()
    source = json.loads((directory / "SOURCE.json").read_text(encoding="utf-8"))
    assert ModelTokenizer.vendored_directory(source["tokenizer_id"]) == directory
    assert {"format", "file", "repo", "revision", "sha256", "license"} <= source.keys()


def test_unknown_tokenizer_raises_naming_it() -> None:
    with pytest.raises(ValueError, match="no-such-tokenizer"):
        ModelTokenizer.from_vendored("no-such-tokenizer")


@pytest.mark.parametrize("tokenizer_id", ["../../etc", "BGE-M3", "bge_m3", ""])
def test_tokenizer_id_cannot_leave_the_vendored_folder(tokenizer_id: str) -> None:
    with pytest.raises(ValueError, match="lowercase letters, digits and dashes"):
        ModelTokenizer.vendored_directory(tokenizer_id)


def test_shared_tokenizers_load_once_per_process() -> None:
    assert ModelTokenizer.shared("bge-m3") is ModelTokenizer.shared("bge-m3")


def test_fallback_counts_like_tiktoken_without_margin() -> None:
    fallback = ModelTokenizer.shared(FALLBACK_TOKENIZER_ID)

    assert fallback.count("hello world") == len(fallback.encode_without_specials("hello world")) == 2
