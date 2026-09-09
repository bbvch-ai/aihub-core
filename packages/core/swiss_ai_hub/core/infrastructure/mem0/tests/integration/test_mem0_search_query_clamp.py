"""Integration test for the search-query clamp (issue #1752).

Requires the dev stack: LiteLLM, the configured embedding model, and Milvus. Opt in with

    set -a; source .env; set +a
    uv run pytest -m integration swiss_ai_hub/core/infrastructure/mem0/tests/integration -v

The unit tests cover the clamp arithmetic against tiktoken. Only a live embedder can show that the
clamped query fits the model's *own* tokenizer, which counts differently — bge-m3 reads 1.6x what
tiktoken reports for English, which is what EMBEDDING_BUDGET_SAFETY_FACTOR has to absorb.
"""

import os
import urllib.request

import pytest

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.memory.user_memory import UserMemory
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

QUESTION = "What is the retention period for invoices?"
REQUIRED_ENV = ("LITE_LLM_PROXY_BASE_URL", "MEM0_LLM_NAME", "MEM0_EMBEDDING_MODEL_NAME", "MILVUS_URL")

QUERIES = {
    "normal": QUESTION,
    # Far past any embedding window, with the real question at the tail the clamp must keep.
    "oversized": ("Invoice archival policy background. " * 8000) + QUESTION,
    # Exotic whitespace resists tiktoken compression but yields no chunks to keep.
    "whitespace-only": " \n\t" * 4000,
    # Short in characters, long in tokens — a character-based budget would miss this.
    "emoji": "\U0001f600" * 5000,
}


def _stack_unavailable() -> str | None:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        return f"unset env: {', '.join(missing)} — run `set -a; source .env; set +a`"
    url = os.environ["LITE_LLM_PROXY_BASE_URL"].rstrip("/") + "/health/liveliness"
    try:
        urllib.request.urlopen(url, timeout=5)
    except Exception as exc:
        return f"{url} unreachable ({type(exc).__name__}) — start the dev stack"
    return None


@pytest.fixture(scope="module")
def user_memory() -> UserMemory:
    reason = _stack_unavailable()
    if reason:
        pytest.skip(reason)
    user = UserIdentity(id="it-1752", name="IT 1752", email="it-1752@example.com", roles=[])
    return UserMemory(user=user, t=LocaleHandler(locale="en"))


@pytest.mark.parametrize("label", list(QUERIES))
async def test_search_completes_whatever_the_query_size(user_memory, label):
    """Before the clamp, the oversized case raised litellm.ContextWindowExceededError and killed the run."""
    result = await user_memory.search_user_memory(query=QUERIES[label], limit=5, rerank=False)

    assert result.results is not None
