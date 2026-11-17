"""Tests for LangfuseProvisioner — Langfuse auto-provisioning on API startup."""

import logging
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.langfuse.langfuse_provisioner import (
    LangfuseProvisioner,
)

PROVISIONER_MODULE = "swiss_ai_hub.core.infrastructure.langfuse.langfuse_provisioner"

LITELLM_MODELS = [
    {"model_name": "text-generation/gemma-4-31B-it", "model_info": {"mode": "chat"}},
    {"model_name": "text-generation/MinerU2.5-2509-1.2B", "model_info": {"mode": "chat"}},
    {"model_name": "text-generation/olmOCR-7B-0725", "model_info": {"mode": "chat"}},
    {"model_name": "text-generation/LightOnOCR-1B", "model_info": {"mode": "chat"}},
    {"model_name": "embedding/bge-m3", "model_info": {"mode": "embedding"}},
    {"model_info": {"mode": "chat"}},
]


def _litellm_settings(internal_base_url: str = "http://litellm:4000", api_key: str | None = "sk-litellm"):
    settings = MagicMock()
    settings.BASE_URL = "http://localhost:4000"
    settings.get_internal_base_url.return_value = internal_base_url
    if api_key is None:
        settings.API_KEY = None
    else:
        settings.API_KEY = MagicMock()
        settings.API_KEY.get_secret_value.return_value = api_key
    return settings


@pytest.fixture
def mock_langfuse_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://langfuse:3000"
    settings.PUBLIC_KEY = "pk-test"
    settings.SECRET_KEY = MagicMock()
    settings.SECRET_KEY.get_secret_value.return_value = "sk-test"
    return settings


@pytest.fixture
def provisioner(mock_langfuse_settings: MagicMock) -> LangfuseProvisioner:
    return LangfuseProvisioner(langfuse_settings=mock_langfuse_settings)


def _ok_response(status_code: int = 200, json_data: dict | None = None) -> httpx.Response:
    """Build a fake httpx.Response."""
    resp = httpx.Response(status_code=status_code, json=json_data or {})
    return resp


def _model_info_response(json_data: dict) -> httpx.Response:
    """`_fetch_litellm_models` calls `raise_for_status`, which needs the originating request attached."""
    return httpx.Response(
        status_code=200,
        json=json_data,
        request=httpx.Request("GET", "http://localhost:4000/v1/model/info"),
    )


class TestProvision:
    """Tests for the main provision() orchestration method."""

    @pytest.mark.asyncio
    async def test_provision_calls_all_steps(self, provisioner: LangfuseProvisioner) -> None:
        with (
            patch.object(provisioner, "_fetch_litellm_models", return_value=[]) as mock_fetch,
            patch.object(provisioner, "_register_aihub_connection") as mock_aihub,
            patch.object(provisioner, "_register_litellm_connection") as mock_litellm,
            patch.object(provisioner, "_register_model_definitions") as mock_models,
            patch.object(provisioner, "_create_default_prompt") as mock_prompt,
        ):
            await provisioner.provision()

            mock_fetch.assert_called_once()
            mock_aihub.assert_called_once()
            mock_litellm.assert_called_once()
            mock_models.assert_called_once()
            mock_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_provision_continues_after_step_failure(self, provisioner: LangfuseProvisioner) -> None:
        """A failing step should not abort subsequent steps."""
        with (
            patch.object(provisioner, "_fetch_litellm_models", side_effect=RuntimeError("boom")),
            patch.object(provisioner, "_register_aihub_connection") as mock_aihub,
            patch.object(provisioner, "_register_litellm_connection") as mock_litellm,
            patch.object(provisioner, "_register_model_definitions") as mock_models,
            patch.object(provisioner, "_create_default_prompt") as mock_prompt,
        ):
            await provisioner.provision()

            # All subsequent steps should still be called
            mock_aihub.assert_called_once()
            mock_litellm.assert_called_once()
            mock_models.assert_called_once()
            mock_prompt.assert_called_once()


class TestSyncAgents:
    """Tests for the sync_agents() method."""

    @pytest.mark.asyncio
    async def test_sync_agents_updates_connection(self, provisioner: LangfuseProvisioner) -> None:
        with patch.object(provisioner, "_upsert_llm_connection") as mock_upsert:
            await provisioner.sync_agents(["agent/rag", "agent/llm"])

            mock_upsert.assert_called_once()
            call_data = mock_upsert.call_args[0][1]
            assert call_data["customModels"] == ["agent/rag", "agent/llm"]

    @pytest.mark.asyncio
    async def test_sync_agents_skips_empty_list(self, provisioner: LangfuseProvisioner) -> None:
        with patch.object(provisioner, "_upsert_llm_connection") as mock_upsert:
            await provisioner.sync_agents([])
            mock_upsert.assert_not_called()


class TestUpsertLLMConnection:
    """Tests for the _upsert_llm_connection helper."""

    @pytest.mark.asyncio
    async def test_upsert_success(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.put.return_value = _ok_response(200)

        await provisioner._upsert_llm_connection(mock_client, {"provider": "test"}, "Test")

        mock_client.put.assert_called_once()
        assert "/llm-connections" in mock_client.put.call_args[0][0]

    @pytest.mark.asyncio
    async def test_upsert_raises_on_error(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        error_resp = httpx.Response(status_code=500, request=httpx.Request("PUT", "http://test"))
        mock_client.put.return_value = error_resp

        with pytest.raises(httpx.HTTPStatusError):
            await provisioner._upsert_llm_connection(mock_client, {}, "Test")

    @pytest.mark.asyncio
    async def test_blocked_address_names_the_allowlist_and_the_hostname(self, provisioner: LangfuseProvisioner) -> None:
        """A bare 400 cost a full debugging cycle downstream — the log must carry the remedy."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.put.return_value = httpx.Response(
            status_code=400,
            json={"message": "Invalid baseURL: Blocked IP address detected", "error": "InvalidRequestError"},
            request=httpx.Request("PUT", "http://test"),
        )

        with pytest.raises(ValueError) as blocked:
            await provisioner._upsert_llm_connection(
                mock_client, {"baseURL": "http://litellm:4000"}, "AI-Hub LLM (Evaluators)"
            )

        message = str(blocked.value)
        assert "LANGFUSE_LLM_CONNECTION_WHITELISTED_HOST" in message
        assert "'litellm'" in message
        assert "langfuse-worker" in message


class TestCreateModelDefinition:
    """Tests for the _create_model_definition helper."""

    @pytest.mark.asyncio
    async def test_create_model_success(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(201)

        result = await provisioner._create_model_definition(mock_client, "gpt-4", 0.001, 0.002)

        assert result is True

    @pytest.mark.asyncio
    async def test_create_model_conflict_returns_false(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(409)

        result = await provisioner._create_model_definition(mock_client, "gpt-4", 0.001, 0.002)

        assert result is False

    @pytest.mark.asyncio
    async def test_create_model_unknown_error_returns_false(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(400)

        result = await provisioner._create_model_definition(mock_client, "gpt-4", 0.001, 0.002)

        assert result is False


GEMMA = "text-generation/gemma-4-31B-it"
GEMMA_PRICED = {"model_name": GEMMA, "model_info": {"input_cost_per_token": 0.001, "output_cost_per_token": 0.002}}


async def _register(
    provisioner: LangfuseProvisioner, litellm_models: list[dict], current_prices: dict[str, tuple[float, float]]
) -> MagicMock:
    with (
        patch.object(provisioner, "_fetch_custom_model_prices", return_value=current_prices),
        patch.object(provisioner, "_create_model_definition", return_value=True) as mock_create,
    ):
        await provisioner._register_model_definitions(AsyncMock(spec=httpx.AsyncClient), litellm_models)
    return mock_create


class TestRegisterModelDefinitions:
    """Tests for _register_model_definitions which iterates LiteLLM models."""

    @pytest.mark.asyncio
    async def test_registers_models_with_pricing(self, provisioner: LangfuseProvisioner) -> None:
        litellm_models = [
            GEMMA_PRICED,
            {
                "model_name": "embedding/bge-m3",
                "model_info": {"input_cost_per_token": 0.0001, "output_cost_per_token": 0.0},
            },
        ]

        mock_create = await _register(provisioner, litellm_models, {})

        assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_models_without_pricing(self, provisioner: LangfuseProvisioner) -> None:
        litellm_models = [
            {"model_name": GEMMA, "model_info": {}},
            {"model_name": "reranker/bge", "model_info": {"mode": "rerank", "input_cost_per_token": None}},
        ]

        mock_create = await _register(provisioner, litellm_models, {})

        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_model_priced_by_input_only_is_registered_with_a_free_output(
        self, provisioner: LangfuseProvisioner
    ) -> None:
        reranker = {"model_name": "reranker/bge", "model_info": {"mode": "rerank", "input_cost_per_token": 7.7e-09}}

        mock_create = await _register(provisioner, [reranker], {})

        mock_create.assert_called_once_with(ANY, "reranker/bge", 7.7e-09, 0, None)

    @pytest.mark.asyncio
    async def test_a_new_model_is_priced_from_its_first_trace(self, provisioner: LangfuseProvisioner) -> None:
        mock_create = await _register(provisioner, [GEMMA_PRICED], {})

        mock_create.assert_called_once_with(ANY, GEMMA, 0.001, 0.002, None)

    @pytest.mark.asyncio
    async def test_an_unchanged_price_is_not_registered_again(self, provisioner: LangfuseProvisioner) -> None:
        mock_create = await _register(provisioner, [GEMMA_PRICED], {GEMMA: (0.001, 0.002)})

        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_changed_price_applies_from_now_on(self, provisioner: LangfuseProvisioner) -> None:
        """Older traces keep the price they were made at, so the new definition starts now."""
        before = datetime.now(UTC)

        mock_create = await _register(provisioner, [GEMMA_PRICED], {GEMMA: (0.0002, 0.0004)})

        start_date = mock_create.call_args.args[4]
        assert start_date >= before


class TestFetchCustomModelPrices:
    @staticmethod
    def _model(name: str, start_date: str | None, input_price: float, *, managed: bool = False) -> dict:
        return {
            "modelName": name,
            "startDate": start_date,
            "isLangfuseManaged": managed,
            "prices": {"input": {"price": input_price}, "output": {"price": input_price * 2}},
        }

    @pytest.mark.asyncio
    async def test_reads_the_newest_custom_definition_of_each_model_across_pages(
        self, provisioner: LangfuseProvisioner
    ) -> None:
        pages = {
            "1": [self._model(GEMMA, None, 0.1), self._model("gpt-4o", None, 9.0, managed=True)],
            "2": [self._model(GEMMA, "2026-11-17T00:00:00Z", 0.3), self._model(GEMMA, "2026-10-01T00:00:00Z", 0.2)],
        }

        def answer(request: httpx.Request) -> httpx.Response:
            page = request.url.params["page"]
            return httpx.Response(200, json={"data": pages[page], "meta": {"page": int(page), "totalPages": 2}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(answer)) as client:
            prices = await provisioner._fetch_custom_model_prices(client)

        assert prices == {GEMMA: (0.3, 0.6)}


class TestCreateModelDefinitionStartDate:
    @pytest.mark.asyncio
    async def test_a_start_date_is_sent_when_given(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(201)
        start_date = datetime(2026, 11, 17, tzinfo=UTC)

        await provisioner._create_model_definition(mock_client, GEMMA, 0.001, 0.002, start_date)

        assert mock_client.post.call_args.kwargs["json"]["startDate"] == start_date.isoformat()


class TestCreatePrompt:
    """Tests for the _create_prompt helper."""

    @pytest.mark.asyncio
    async def test_create_prompt_success(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(201)

        await provisioner._create_prompt(
            mock_client, name="test-prompt", messages=[{"role": "user", "content": "hi"}], labels=[], tags=[]
        )

        mock_client.post.assert_called_once()
        assert "/prompts" in mock_client.post.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_prompt_conflict_is_silent(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(409)

        # Should not raise
        await provisioner._create_prompt(
            mock_client, name="test-prompt", messages=[{"role": "user", "content": "hi"}], labels=[], tags=[]
        )


class TestJudgeModels:
    """LiteLLM reports OCR/VLM models as `mode: chat`, but they cannot grade text."""

    def test_excludes_ocr_models(self) -> None:
        assert LangfuseProvisioner._judge_models(LITELLM_MODELS) == ["text-generation/gemma-4-31B-it"]

    def test_excludes_non_chat_modes(self) -> None:
        models = [{"model_name": "embedding/bge-m3", "model_info": {"mode": "embedding"}}]
        assert LangfuseProvisioner._judge_models(models) == []

    def test_ignores_entries_without_a_model_name(self) -> None:
        assert LangfuseProvisioner._judge_models([{"model_info": {"mode": "chat"}}]) == []

    def test_ocr_match_is_case_insensitive(self) -> None:
        models = [{"model_name": "text-generation/mineru2.5-2509-1.2b", "model_info": {"mode": "chat"}}]
        assert LangfuseProvisioner._judge_models(models) == []

    def test_keeps_a_model_that_merely_contains_an_ocr_name(self) -> None:
        """The rule is a prefix on the bare name, not a substring anywhere."""
        models = [{"model_name": "text-generation/reviewer-olmocr-8B", "model_info": {"mode": "chat"}}]
        assert LangfuseProvisioner._judge_models(models) == ["text-generation/reviewer-olmocr-8B"]


class TestRegisterLiteLLMConnection:
    """Langfuse dials this connection from its own container, so it carries the URL reachable from there."""

    @pytest.mark.asyncio
    async def test_registers_the_langfuse_facing_url_not_the_api_side_one(
        self, provisioner: LangfuseProvisioner
    ) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings()),
            patch.object(provisioner, "_upsert_llm_connection") as mock_upsert,
        ):
            await provisioner._register_litellm_connection(mock_client, LITELLM_MODELS)

        connection_data = mock_upsert.call_args[0][1]
        assert connection_data["baseURL"] == "http://litellm:4000"
        assert "localhost:4000" not in str(connection_data)

    @pytest.mark.asyncio
    async def test_custom_models_exclude_ocr_entries(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings()),
            patch.object(provisioner, "_upsert_llm_connection") as mock_upsert,
        ):
            await provisioner._register_litellm_connection(mock_client, LITELLM_MODELS)

        assert mock_upsert.call_args[0][1]["customModels"] == ["text-generation/gemma-4-31B-it"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("loopback", ["http://localhost:4000", "http://127.0.0.1:4000", "http://[::1]:4000"])
    async def test_raises_when_the_url_is_loopback(self, provisioner: LangfuseProvisioner, loopback: str) -> None:
        """Falling back to the host-side BASE_URL in dev would register a URL that only reaches Langfuse itself."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch(
                f"{PROVISIONER_MODULE}.LiteLLMProxySettings",
                return_value=_litellm_settings(internal_base_url=loopback),
            ),
            patch.object(provisioner, "_upsert_llm_connection") as mock_upsert,
            pytest.raises(ValueError, match="LITE_LLM_PROXY_INTERNAL_BASE_URL"),
        ):
            await provisioner._register_litellm_connection(mock_client, LITELLM_MODELS)

        mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_api_key_is_unset(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings(api_key=None)),
            patch.object(provisioner, "_upsert_llm_connection") as mock_upsert,
            pytest.raises(ValueError, match="LITE_LLM_PROXY_API_KEY"),
        ):
            await provisioner._register_litellm_connection(mock_client, LITELLM_MODELS)

        mock_upsert.assert_not_called()


class TestFetchLiteLLMModels:
    """Discovery is a server-to-server call from this process, so it stays on the API-side BASE_URL."""

    @pytest.mark.asyncio
    async def test_queries_the_api_side_url_not_the_langfuse_facing_one(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _model_info_response({"data": LITELLM_MODELS})

        with patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings()):
            models = await LangfuseProvisioner._fetch_litellm_models(mock_client)

        assert models == LITELLM_MODELS
        url = mock_client.get.call_args[0][0]
        assert url == "http://localhost:4000/v1/model/info"
        assert mock_client.get.call_args[1]["headers"]["Authorization"] == "Bearer sk-litellm"

    @pytest.mark.asyncio
    async def test_propagates_http_errors_rather_than_returning_an_empty_list(self) -> None:
        """Swallowing this used to report zero judge models as though LiteLLM had none."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = httpx.Response(
            status_code=503, request=httpx.Request("GET", "http://litellm:4000/v1/model/info")
        )

        with (
            patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings()),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await LangfuseProvisioner._fetch_litellm_models(mock_client)

    @pytest.mark.asyncio
    async def test_missing_api_key_sends_an_empty_bearer(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _model_info_response({})

        with patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings(api_key=None)):
            assert await LangfuseProvisioner._fetch_litellm_models(mock_client) == []

        assert mock_client.get.call_args[1]["headers"]["Authorization"] == "Bearer "


class TestRegisterAihubConnection:
    """Startup registers the agents connection with no models; the discovery loop fills it in."""

    @pytest.mark.asyncio
    async def test_registers_with_an_empty_model_list(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch.object(provisioner, "_upsert_llm_connection") as mock_upsert:
            await provisioner._register_aihub_connection(mock_client)

        connection_data = mock_upsert.call_args[0][1]
        assert connection_data["provider"] == "ai-hub-agents"
        assert connection_data["customModels"] == []


class TestBuildAihubConnectionData:
    """The agents connection is dialled from the Langfuse container just as the evaluator one is."""

    def test_raises_when_the_agent_url_is_loopback(self, provisioner: LangfuseProvisioner) -> None:
        settings = MagicMock()
        settings.OPENAI_API_BASE_URL = "http://localhost:8000/api/v1/active/openai"

        with (
            patch(f"{PROVISIONER_MODULE}.AIHubSettings", return_value=settings),
            pytest.raises(ValueError, match="AIHUB_OPENAI_API_BASE_URL"),
        ):
            provisioner._build_aihub_connection_data(custom_models=[])


class TestRunStep:
    """A silently dead feature cost a full debugging cycle downstream — failures must be loud."""

    @pytest.mark.asyncio
    async def test_failure_is_logged_at_error(self, caplog: pytest.LogCaptureFixture) -> None:
        async def boom() -> None:
            raise RuntimeError("upstream rejected the connection")

        with caplog.at_level(logging.ERROR):
            result = await LangfuseProvisioner._run_step("LiteLLM connection", boom())

        assert result is None
        errors = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert errors
        assert "LiteLLM connection" in errors[0].getMessage()
        assert errors[0].exc_info is not None, "the traceback must survive — the message alone rarely locates the cause"
