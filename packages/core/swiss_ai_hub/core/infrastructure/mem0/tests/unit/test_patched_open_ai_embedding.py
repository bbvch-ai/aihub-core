from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.mem0.patched_open_ai_embedding import PatchedOpenAIEmbedding


@pytest.fixture
def embedding() -> tuple[PatchedOpenAIEmbedding, MagicMock]:
    client = MagicMock()
    client.embeddings.create.return_value = SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])
    source = SimpleNamespace(config=SimpleNamespace(model="embedding/test"), client=client)
    with patch("swiss_ai_hub.core.infrastructure.mem0.patched_open_ai_embedding.tiktoken.get_encoding") as get_encoding:
        tokenizer = MagicMock()
        tokenizer.encode.side_effect = lambda text: list(text)
        tokenizer.decode.side_effect = lambda tokens: "".join(tokens)
        get_encoding.return_value = tokenizer
        wrapped = PatchedOpenAIEmbedding.from_embedding(source)
    return wrapped, client


@pytest.mark.parametrize("memory_action", ["add", "search", "update"])
def test_embed_truncates_each_memory_action(embedding, memory_action):
    wrapped, client = embedding
    wrapped._max_input_tokens = 3

    wrapped.embed("ab\ncd", memory_action=memory_action)

    client.embeddings.create.assert_called_once_with(input=["ab "], model="embedding/test")


def test_embed_replaces_newlines_and_passes_short_input(embedding):
    wrapped, client = embedding
    wrapped._max_input_tokens = 10

    wrapped.embed("short\ntext", memory_action="search")

    client.embeddings.create.assert_called_once_with(input=["short text"], model="embedding/test")


def test_embed_without_limit_preserves_untruncated_behavior(embedding):
    wrapped, client = embedding

    wrapped.embed("long\ntext", memory_action="update")

    client.embeddings.create.assert_called_once_with(input=["long text"], model="embedding/test")
    wrapped._tokenizer.encode.assert_not_called()
    wrapped._tokenizer.decode.assert_not_called()
