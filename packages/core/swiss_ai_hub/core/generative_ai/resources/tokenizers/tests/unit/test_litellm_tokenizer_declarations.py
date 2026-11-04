"""Apps read `aihub_tokenizer` from the LiteLLM config they run against. An embedder or reranker that lost the key
would silently fall back to tiktoken sizing, and one naming a tokenizer nobody vendored would fail every budget
site, so every generated config is checked here."""

from pathlib import Path

import pytest
import yaml

from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import INPUT_OVERHEAD_KEY, TOKENIZER_KEY
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer

REPO_ROOT = Path(__file__).resolve().parents[9]
GENERATED_CONFIGS = sorted((REPO_ROOT / "infra/configs/litellm").glob("litellm-config.*.yml"))
COUNTED_MODES = {"embedding", "rerank"}


def _counted_models(config_file: Path) -> list[dict]:
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    return [entry for entry in config["model_list"] if entry.get("model_info", {}).get("mode") in COUNTED_MODES]


def test_generated_configs_are_found() -> None:
    assert GENERATED_CONFIGS


@pytest.mark.parametrize("config_file", GENERATED_CONFIGS, ids=[path.name for path in GENERATED_CONFIGS])
def test_every_embedding_and_rerank_model_declares_a_vendored_tokenizer(config_file: Path) -> None:
    models = _counted_models(config_file)

    assert models
    for entry in models:
        model_info = entry["model_info"]
        assert ModelTokenizer.is_vendored(model_info[TOKENIZER_KEY]), entry["model_name"]
        assert model_info[INPUT_OVERHEAD_KEY] == (4 if model_info["mode"] == "rerank" else 2), entry["model_name"]
