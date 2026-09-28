"""Live test of the ``aihub_turn_scope_filter`` OpenWebUI function (aihub-core-private#147).

Drives OpenWebUI's own ``/api/chat/completions`` the way the chat frontend does — the whole conversation's files in
``files``, the message being answered in ``user_message`` — and reads back which documents the model was given. The
filter sits in front of everything that consumes ``metadata["files"]`` (OpenWebUI's file-context injection and the
``__files__`` the AI-Hub pipe forwards), so a plain LiteLLM-backed workspace model with the agent id prefix exercises
the exact path an agent model takes, without needing the agent runtime.

Requires the dev docker stack (OpenWebUI, LiteLLM) with the filter registered by ``openwebui-init``. Opt in with

    set -a; source .env; set +a
    uv run pytest -m integration swiss_ai_hub/core/infrastructure/openwebui/tests/integration -v

Documents are handed over inline (``context: "full"``) so the test needs no upload, extraction or embedding — with
``RAG_FULL_CONTEXT`` on, the production path ends in the same place: the complete document text in the prompt.
"""

import os
import re
import uuid
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

pytestmark = pytest.mark.integration

FILTER_ID = "aihub-turn-scope-filter"
AGENT_MODEL_PREFIX = "aihub-agent-"
# A provisioner-created plain workspace model, not the raw LiteLLM id: with admin access control on, OpenWebUI
# answers "Model not found" for a base model that has no workspace entry, even to an admin.
PLAIN_MODEL = os.environ.get("OPENWEBUI_IT_PLAIN_MODEL", "aihub-model-text-generation-Qwen3.5-122B-A10B-FP8")
QUESTION = (
    "List every reference code that appears in the documents provided to you. "
    "Reply with the codes only, comma-separated, nothing else."
)
DOCUMENTS = {
    "alpha": ("policy_alpha.md", "ALPHA7731"),
    "bravo": ("policy_bravo.md", "BRAVO2290"),
    "charlie": ("policy_charlie.md", "CHARLIE5518"),
}
NAMESPACE = uuid.UUID("6f2f0a1e-147c-4c57-9c1e-a1b0b0000147")


def _stack_unavailable() -> str | None:
    try:
        settings = OpenWebuiSettings()
    except Exception as exc:
        return f"OpenWebUI settings unavailable ({type(exc).__name__}) — run `set -a; source .env; set +a`"
    try:
        httpx.get(f"{settings.BASE_URL.rstrip('/')}/health", timeout=5.0).raise_for_status()
    except Exception as exc:
        return f"{settings.BASE_URL} unreachable ({type(exc).__name__}) — start the dev stack"
    return None


@pytest.fixture(scope="module")
def client() -> Iterator[httpx.Client]:
    reason = _stack_unavailable()
    if reason:
        pytest.skip(reason)
    settings = OpenWebuiSettings()
    token = OpenWebuiTokenService.generate_token(
        settings.SECRET_KEY.get_secret_value(), user_id=settings.SERVICE_ACCOUNT_ID, ttl_seconds=3600
    )
    with httpx.Client(
        base_url=settings.BASE_URL.rstrip("/"),
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx.Timeout(connect=5.0, read=240.0, write=30.0, pool=5.0),
    ) as http:
        functions = {f["id"]: f for f in http.get("/api/v1/functions/").raise_for_status().json()}
        registered = functions.get(FILTER_ID)
        if not registered or not registered["is_active"] or not registered["is_global"]:
            pytest.skip(f"{FILTER_ID} not active+global in OpenWebUI — run the openwebui-init container")
        model_ids = {m["id"] for m in http.get("/api/models").raise_for_status().json()["data"]}
        if PLAIN_MODEL not in model_ids:
            pytest.skip(f"{PLAIN_MODEL} not offered by OpenWebUI — set OPENWEBUI_IT_PLAIN_MODEL")
        yield http


def _base_model_id(client: httpx.Client, workspace_model_id: str) -> str:
    models = client.get("/api/models").raise_for_status().json()["data"]
    entry = next(m for m in models if m["id"] == workspace_model_id)
    return (entry.get("info") or {}).get("base_model_id") or workspace_model_id


@pytest.fixture(scope="module")
def agent_model(client: httpx.Client) -> Iterator[str]:
    """A workspace model carrying the provisioner's agent prefix, backed by the same LiteLLM model as PLAIN_MODEL."""
    model_id = f"{AGENT_MODEL_PREFIX}ittest-turn-scope-{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/v1/models/create",
        json={
            "id": model_id,
            "base_model_id": _base_model_id(client, PLAIN_MODEL),
            "name": "IT turn scope",
            "meta": {"description": "integration test model for aihub_turn_scope_filter"},
            "params": {},
        },
    ).raise_for_status()
    # Chat completions resolve models from an in-memory cache that ``/api/models`` refreshes; until then the
    # freshly created model answers "Model not found".
    listed = {m["id"] for m in client.get("/api/models").raise_for_status().json()["data"]}
    assert model_id in listed, f"{model_id} not listed after creation"
    try:
        yield model_id
    finally:
        client.post("/api/v1/models/model/delete", json={"id": model_id})


def _document(key: str) -> dict[str, Any]:
    name, code = DOCUMENTS[key]
    return {
        "type": "file",
        "id": str(uuid.uuid5(NAMESPACE, key)),
        "name": name,
        "context": "full",
        "file": {
            "data": {"content": f"# {name}\n\nInternal policy {key}. Reference code {code}.\n"},
            "meta": {"name": name},
        },
    }


def _attached(key: str) -> dict[str, Any]:
    return {"type": "file", "id": str(uuid.uuid5(NAMESPACE, key)), "name": DOCUMENTS[key][0]}


def _complete(client: httpx.Client, model: str, current_turn: list[str]) -> str:
    response = client.post(
        "/api/chat/completions",
        json={
            "model": model,
            "chat_id": f"local:it-turn-scope-{uuid.uuid4().hex[:8]}",
            "messages": [{"role": "user", "content": QUESTION}],
            "files": [_document(key) for key in DOCUMENTS],
            "user_message": {
                "id": f"user-{uuid.uuid4().hex[:8]}",
                "role": "user",
                "content": QUESTION,
                "files": [_attached(key) for key in current_turn],
            },
            "stream": False,
        },
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"]
    return re.sub(r"[^A-Z0-9]", "", answer.upper())


def _codes(*keys: str) -> set[str]:
    return {DOCUMENTS[key][1] for key in keys}


def _assert_answers_from(answer: str, present: set[str], absent: set[str]) -> None:
    assert all(code in answer for code in present), f"expected {present} in {answer!r}"
    assert not any(code in answer for code in absent), f"expected none of {absent} in {answer!r}"


def test_should_answer_from_the_attached_file_only_when_turn_attaches_one(client, agent_model):
    """The #147 scenario: two earlier documents in the conversation, one attached now."""
    answer = _complete(client, agent_model, current_turn=["charlie"])

    _assert_answers_from(answer, present=_codes("charlie"), absent=_codes("alpha", "bravo"))


def test_should_keep_every_file_of_the_turn_when_several_are_attached(client, agent_model):
    answer = _complete(client, agent_model, current_turn=["bravo", "charlie"])

    _assert_answers_from(answer, present=_codes("bravo", "charlie"), absent=_codes("alpha"))


def test_should_keep_the_whole_conversation_when_turn_attaches_nothing(client, agent_model):
    """Follow-up questions about earlier documents must keep working."""
    answer = _complete(client, agent_model, current_turn=[])

    _assert_answers_from(answer, present=_codes("alpha", "bravo", "charlie"), absent=set())


def test_should_leave_plain_models_untouched(client):
    """No side effect on models without the agent prefix: OpenWebUI's own behaviour is preserved."""
    answer = _complete(client, PLAIN_MODEL, current_turn=["charlie"])

    _assert_answers_from(answer, present=_codes("alpha", "bravo", "charlie"), absent=set())
