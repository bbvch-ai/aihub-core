from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"

_QWEN = "text-generation/Qwen3.5-122B-A10B-FP8"
_IDENTITY_KEY = "lib.prompt.model.identity_system_message"
_THREAD_ID = "507f1f77bcf86cd799439011"

# The reproduction from issue #144: the user asked Kimi first, switched model, and asked again. OpenWebUI
# forwards one history across the switch, so the next model reads a Kimi self-identification as its own turn.
_CONTAMINATED_HISTORY: list[dict] = [
    {"role": "user", "content": "who are you"},
    {"role": "assistant", "content": "I am Kimi, an AI assistant created by Moonshot AI."},
    {"role": "user", "content": "who are you"},
]


def _hub_request(messages: list[dict], model: str = _QWEN) -> ChatCompletionRequest:
    """A request as `openai_pipeline` sends it: carrying the AI Hub `thread_id` extension."""
    return ChatCompletionRequest(model=model, messages=messages, metadata={"thread_id": _THREAD_ID})


def _roles(request: ChatCompletionRequest) -> list[str]:
    return [message["role"] for message in request.messages]


def _en() -> LocaleHandler:
    return LocaleHandler(locale="en")


class TestIdentitySystemMessage:
    def test_leads_the_message_list(self):
        request = _hub_request(list(_CONTAMINATED_HISTORY))

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert _roles(request) == ["system", "user", "assistant", "user"]

    def test_names_the_selected_model_without_its_capability_prefix(self):
        request = _hub_request(list(_CONTAMINATED_HISTORY))

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert "Qwen3.5-122B-A10B-FP8" in request.messages[0]["content"]
        assert "text-generation/" not in request.messages[0]["content"]

    def test_keeps_a_model_name_that_carries_no_capability_prefix(self):
        request = _hub_request(list(_CONTAMINATED_HISTORY), model="gemma-4-31B-it")

        OpenaiService._apply_model_identity(request, "gemma-4-31B-it", _en())

        assert "gemma-4-31B-it" in request.messages[0]["content"]

    def test_leaves_the_original_history_untouched(self):
        request = _hub_request(list(_CONTAMINATED_HISTORY))

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert request.messages[1:] == _CONTAMINATED_HISTORY

    def test_orders_a_client_system_prompt_after_ours(self):
        """A caller's own system prompt must survive and stay later in the list, so it still wins on task
        behaviour while the platform identity is merely the default."""
        client_prompt = {"role": "system", "content": "You only answer in haiku."}
        request = _hub_request([client_prompt, *_CONTAMINATED_HISTORY])

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert _roles(request) == ["system", "system", "user", "assistant", "user"]
        assert request.messages[1] == client_prompt

    def test_tolerates_a_request_without_messages(self):
        request = _hub_request([])
        request.messages = None

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert _roles(request) == ["system"]

    @pytest.mark.parametrize("locale", LocaleHandler.LOCALE_WHITE_LIST)
    def test_every_locale_defines_the_prompt(self, locale: str):
        """`t_object` reads `lib/prompt.{locale}.yml` directly, so a locale missing the key raises here
        instead of silently falling back to another language."""
        template = LocaleHandler(locale=locale).t_object(_IDENTITY_KEY, locale=locale)

        assert "{model_name}" in template


class TestEveryPlainModelRequestGetsAnIdentity:
    """Gating on the AI Hub-only `metadata.thread_id` was tried and reverted: OpenWebUI does not reach this
    endpoint through `openai_pipeline`, it reaches it through its own native OpenAI connection
    (`OPENAI_API_BASE_URL`), whose payload carries no `metadata` at all. Verified live — with the gate in
    place, issue #144 still reproduced in the browser. There is no field that separates the hub's own chat
    from an external SDK client, so injection is unconditional."""

    def test_a_request_without_metadata_is_still_injected(self):
        request = ChatCompletionRequest(model=_QWEN, messages=list(_CONTAMINATED_HISTORY))

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert _roles(request) == ["system", "user", "assistant", "user"]
        assert "Qwen3.5-122B-A10B-FP8" in request.messages[0]["content"]

    def test_metadata_without_a_thread_id_is_still_injected(self):
        request = ChatCompletionRequest(
            model=_QWEN, messages=list(_CONTAMINATED_HISTORY), metadata={"display_id": _THREAD_ID}
        )

        OpenaiService._apply_model_identity(request, _QWEN, _en())

        assert _roles(request) == ["system", "user", "assistant", "user"]


class TestAssistantsKeepTheirOwnIdentity:
    """`chat_completion_with_assistants` reaches its agent branch only via `chat_completion`'s 404, so the
    injection must sit after `get_model`. Agents answer identity questions from their own workflow
    definition (ADR 2026_06_04) and must not be handed a contradicting persona. Both requests carry a
    `thread_id`, so the assertions fail if the ordering breaks rather than passing on the hub gate."""

    @pytest.mark.asyncio
    async def test_unknown_model_raises_404_before_injecting(self):
        agent_model = "MyAgent/507f1f77bcf86cd799439011"
        request = _hub_request(list(_CONTAMINATED_HISTORY), model=agent_model)
        not_a_model = HTTPException(status_code=404, detail=f"Model {agent_model} not found.")

        with patch.object(OpenaiService, "get_model", new=AsyncMock(side_effect=not_a_model)):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.chat_completion(
                    model_name=agent_model,
                    chat_completion_request=request,
                    user=fake_user(),
                    t=_en(),
                )

        assert exc.value.status_code == 404
        assert request.messages == _CONTAMINATED_HISTORY

    @pytest.mark.asyncio
    async def test_denied_model_raises_403_before_injecting(self):
        request = _hub_request(list(_CONTAMINATED_HISTORY))

        with (
            patch.object(OpenaiService, "get_model", new=AsyncMock()),
            patch(
                f"{_SERVICE}.AccessChecker.from_user",
                return_value=AccessChecker([], tenant_access_rules=["aihub.admin.>"]),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.chat_completion(
                    model_name=_QWEN,
                    chat_completion_request=request,
                    user=fake_user(),
                    t=_en(),
                )

        assert exc.value.status_code == 403
        assert request.messages == _CONTAMINATED_HISTORY
