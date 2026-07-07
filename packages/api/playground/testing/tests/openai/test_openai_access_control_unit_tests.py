from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_CONTROLLER = "swiss_ai_hub.api.routes.openai.openai_controller"
_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"

# Tenant allows everything; the user's own rules are what each test varies.
_TENANT_FULL = ["aihub.admin.>"]


def _checker(user_rules: list[str]) -> AccessChecker:
    return AccessChecker(user_rules, tenant_access_rules=_TENANT_FULL)


def _route_endpoint(builder_method: str):
    """Builds a controller with only ``builder_method`` mounted and returns its single route's raw
    endpoint, so a route handler closure can be unit-tested directly (Security/Depends bypassed)."""
    controller = OpenaiController(auth=TestAuthHandler())
    getattr(controller, builder_method)()
    route = next(r for r in controller.router.routes if isinstance(r, APIRoute))
    return route.endpoint


class TestAssertModelAccessHelper:
    """Covers the shared guard, now on the service so internal callers (not just HTTP) enforce it."""

    def test_allows_granted_capability(self):
        with patch(
            f"{_SERVICE}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.text-generation.*"])
        ):
            OpenaiService._assert_model_access(fake_user(), "text-generation/gemma-4-31B-it")  # no raise

    def test_denies_other_capability(self):
        with patch(
            f"{_SERVICE}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.text-generation.*"])
        ):
            with pytest.raises(HTTPException) as exc:
                OpenaiService._assert_model_access(fake_user(), "embedding/bge-m3")
        assert exc.value.status_code == 403

    def test_denies_bare_name_without_capability(self):
        with patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.>"])):
            with pytest.raises(HTTPException) as exc:
                OpenaiService._assert_model_access(fake_user(), "transcription")  # no slash -> empty name
        assert exc.value.status_code == 403


class TestServiceInvocationEnforcesModelAccess:
    """Each invocation method must enforce access itself, before any model call, so a direct
    (non-HTTP) caller cannot bypass the guard the controller used to run."""

    @pytest.mark.asyncio
    async def test_embeddings_denies_without_access(self):
        with patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.get_embeddings(model_name="embedding/bge-m3", input_text="hi", user=fake_user())
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_stt_denies_without_access(self):
        with patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.stt(
                    model_name="whisper-large-v3",
                    file=Mock(),
                    user=fake_user(),
                    language=None,
                    prompt=None,
                    response_format="json",
                    temperature=0,
                    timestamp_granularities=None,
                )
        assert exc.value.status_code == 403


class TestChatCompletionModelAccess:
    @pytest.mark.asyncio
    async def test_denies_unpermitted_model(self):
        with (
            patch.object(OpenaiService, "get_model", new=AsyncMock()),  # model exists
            patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])),  # user granted nothing
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.chat_completion(
                    model_name="text-generation/gemma-4-31B-it",
                    chat_completion_request=Mock(),
                    user=fake_user(),
                    t=Mock(),
                )
        assert exc.value.status_code == 403
        assert "model" in exc.value.detail


class TestChatCompletionWithAssistantsBranching:
    async def _call_with_assistants(self, model_name: str):
        return await OpenaiService.chat_completion_with_assistants(
            model_name=model_name,
            chat_completion_request=Mock(),
            user=fake_user(),
            nc=Mock(),
            usage_limits=Mock(),
            external_agent_event_distributor=Mock(),
            t=Mock(),
        )

    @pytest.mark.asyncio
    async def test_denies_unpermitted_assistant(self):
        """Name is not a model (404) -> falls through to agent branch -> denied agent -> 403."""
        with (
            patch.object(
                OpenaiService,
                "chat_completion",
                new=AsyncMock(side_effect=HTTPException(status_code=404, detail="not found")),
            ),
            patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])),
        ):
            with pytest.raises(HTTPException) as exc:
                await self._call_with_assistants("ResearchAgent/inst1")
        assert exc.value.status_code == 403
        assert "assistant" in exc.value.detail

    @pytest.mark.asyncio
    async def test_model_denial_propagates_and_is_not_masked_as_assistant(self):
        """A 403 from the model path must propagate, NOT be swallowed and retried as an agent."""
        with patch.object(
            OpenaiService,
            "chat_completion",
            new=AsyncMock(side_effect=HTTPException(status_code=403, detail="no access to model")),
        ):
            with pytest.raises(HTTPException) as exc:
                await self._call_with_assistants("text-generation/gemma-4-31B-it")
        assert exc.value.status_code == 403
        assert exc.value.detail == "no access to model"


class TestGetModelsControllerFilter:
    """The `/v1/models` list filter — a different code path from ModelService (partition/slice)."""

    @pytest.mark.asyncio
    async def test_filters_by_capability_and_skips_bare_ids(self):
        endpoint = _route_endpoint("get_models")
        models = SimpleNamespace(
            data=[
                SimpleNamespace(id="text-generation/gemma-4-31B-it"),  # granted
                SimpleNamespace(id="embedding/bge-m3"),  # other capability -> denied
                SimpleNamespace(id="bare-id-without-slash"),  # empty name -> must be skipped, not crash
            ]
        )
        with (
            patch.object(OpenaiService, "get_models", new=AsyncMock(return_value=models)),
            patch(
                f"{_CONTROLLER}.AccessChecker.from_user",
                return_value=_checker(["aihub.user.model.text-generation.*"]),
            ),
        ):
            result = await endpoint(user=fake_user())

        assert [m.id for m in result.data] == ["text-generation/gemma-4-31B-it"]


class TestGetModelWithAssistantsControllerAccess:
    """The `/v1/models/{name}` detail endpoint — model vs assistant access, 403 (not 500) on denial."""

    async def _call(self, model, user_rules: list[str]):
        endpoint = _route_endpoint("get_model_with_assistants")
        with (
            patch.object(OpenaiService, "get_model_with_assistants", new=AsyncMock(return_value=model)),
            patch(f"{_CONTROLLER}.AccessChecker.from_user", return_value=_checker(user_rules)),
        ):
            return await endpoint(full_path=model.id, user=fake_user(), t=Mock())

    @pytest.mark.asyncio
    async def test_denies_unpermitted_model_with_403(self):
        model = SimpleNamespace(id="text-generation/gemma-4-31B-it", object="model", agent_class=None, agent_id=None)
        with pytest.raises(HTTPException) as exc:
            await self._call(model, user_rules=[])
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_denies_unpermitted_assistant_with_403(self):
        model = SimpleNamespace(
            id="ResearchAgent/inst1", object="assistant", agent_class="ResearchAgent", agent_id="inst1"
        )
        with pytest.raises(HTTPException) as exc:
            await self._call(model, user_rules=[])
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_allows_permitted_model(self):
        model = SimpleNamespace(id="text-generation/gemma-4-31B-it", object="model", agent_class=None, agent_id=None)
        result = await self._call(model, user_rules=["aihub.user.model.text-generation.*"])
        assert result is model


class TestGetModelWithAssistantsServiceFallback:
    """Service-level: only a 404 from the model lookup may fall through to the agent branch."""

    @pytest.mark.asyncio
    async def test_non_404_from_model_lookup_propagates(self):
        with patch.object(
            OpenaiService, "get_model", new=AsyncMock(side_effect=HTTPException(status_code=403, detail="denied"))
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.get_model_with_assistants(model_name="text-generation/gemma-4-31B-it", t=Mock())
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_404_falls_through_to_agent_branch(self):
        agent = SimpleNamespace(agent_class="ResearchAgent", agent_id="inst1", is_conversational=True)
        with (
            patch.object(
                OpenaiService, "get_model", new=AsyncMock(side_effect=HTTPException(status_code=404, detail="nf"))
            ),
            patch(f"{_SERVICE}.AgentService.get_agent_instance", new=AsyncMock(return_value=agent)),
        ):
            result = await OpenaiService.get_model_with_assistants(model_name="ResearchAgent/inst1", t=Mock())

        assert result.object == "assistant"
        assert result.agent_id == "inst1"
