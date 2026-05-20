"""Smoke-test every text-generation/* model the LiteLLM proxy advertises.

Discovery is dynamic: the proxy's GET /v1/models is queried at collection time and the
returned text-generation/* ids parametrize the test. For each model we issue a tiny
chat completion and assert a non-empty response, confirming the upstream model resolves
end-to-end through LiteLLM.

Run with the dev docker stack up (LiteLLM healthy) and Swiss LLM Cloud creds in .env:
    uv run pytest -m integration \
        swiss_ai_hub/core/infrastructure/litellm/tests/integration/test_text_generation_models.py -v

Marked `integration` so the default `make test` (-m unit) skips it.
"""

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

pytestmark = pytest.mark.integration

_TEXT_GEN_PREFIX = "text-generation/"
_UNREACHABLE_SENTINEL = "__litellm_unreachable__"


def _list_text_generation_models() -> list[str]:
    try:
        settings = LiteLLMProxySettings()
    except Exception:
        return []
    if settings.API_KEY is None:
        return []
    try:
        with httpx.Client(
            base_url=settings.BASE_URL,
            headers={"Authorization": f"Bearer {settings.API_KEY.get_secret_value()}"},
            timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0),
        ) as client:
            response = client.get("/v1/models")
            response.raise_for_status()
    except Exception:
        return []
    return sorted(m["id"] for m in response.json().get("data", []) if m["id"].startswith(_TEXT_GEN_PREFIX))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "model_name" not in metafunc.fixturenames:
        return
    models = _list_text_generation_models()
    metafunc.parametrize("model_name", models or [_UNREACHABLE_SENTINEL])


def test_text_generation_model_responds(model_name: str) -> None:
    if model_name == _UNREACHABLE_SENTINEL:
        pytest.skip(
            "LiteLLM proxy unreachable, unauthenticated, or no text-generation/* models "
            "registered — start the dev stack and set LITE_LLM_PROXY_BASE_URL / _API_KEY."
        )

    settings = LiteLLMProxySettings()
    with httpx.Client(
        base_url=settings.BASE_URL,
        headers={"Authorization": f"Bearer {settings.API_KEY.get_secret_value()}"},
        timeout=httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0),
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
                # Generous budget so reasoning models (Kimi, Qwen3) can finish thinking
                # and still emit visible content before hitting the limit.
                "max_tokens": 256,
                "temperature": 0,
            },
        )

    assert response.status_code == 200, f"{model_name}: HTTP {response.status_code}\n{response.text[:500]}"
    body = response.json()
    choices = body.get("choices") or []
    assert choices, f"{model_name}: response has no choices: {body}"
    message = choices[0].get("message") or {}
    # Accept either standard `content` or `reasoning_content` (emitted by reasoning models
    # like Kimi-K2.6, Qwen3.5, OpenAI o-series) — both prove the model resolved and produced text.
    text = (message.get("content") or "") + (message.get("reasoning_content") or "")
    assert text.strip(), f"{model_name}: empty content/reasoning in response: {body}"
