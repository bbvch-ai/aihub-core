"""Tests for LangfuseProvisioner — Langfuse auto-provisioning on API startup."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

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


def _litellm_settings(public_url: str | None = "https://litellm.example.com", api_key: str | None = "sk-litellm"):
    settings = MagicMock()
    settings.BASE_URL = "http://litellm:4000"
    settings.PUBLIC_URL = public_url
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


class TestRegisterModelDefinitions:
    """Tests for _register_model_definitions which iterates LiteLLM models."""

    @pytest.mark.asyncio
    async def test_registers_models_with_pricing(self, provisioner: LangfuseProvisioner) -> None:
        litellm_models = [
            {
                "model_name": "text-generation/gemma-4-31B-it",
                "model_info": {"input_cost_per_token": 0.001, "output_cost_per_token": 0.002},
            },
            {
                "model_name": "embedding/bge-m3",
                "model_info": {"input_cost_per_token": 0.0001, "output_cost_per_token": 0.0},
            },
        ]
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch.object(provisioner, "_create_model_definition", return_value=True) as mock_create:
            await provisioner._register_model_definitions(mock_client, litellm_models)

            assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_models_without_pricing(self, provisioner: LangfuseProvisioner) -> None:
        litellm_models = [
            {"model_name": "text-generation/gemma-4-31B-it", "model_info": {}},
            {"model_name": "reranker/bge", "model_info": {"mode": "rerank"}},
        ]
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch.object(provisioner, "_create_model_definition", return_value=True) as mock_create:
            await provisioner._register_model_definitions(mock_client, litellm_models)

            mock_create.assert_not_called()


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
    """Langfuse dials this connection from its own container, so it must carry the public URL."""

    @pytest.mark.asyncio
    async def test_registers_the_public_url_never_the_cluster_url(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings()),
            patch.object(provisioner, "_upsert_llm_connection") as mock_upsert,
        ):
            await provisioner._register_litellm_connection(mock_client, LITELLM_MODELS)

        connection_data = mock_upsert.call_args[0][1]
        assert connection_data["baseURL"] == "https://litellm.example.com"
        assert "http://litellm:4000" not in str(connection_data)

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
    async def test_raises_when_public_url_is_unset(self, provisioner: LangfuseProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch(f"{PROVISIONER_MODULE}.LiteLLMProxySettings", return_value=_litellm_settings(public_url=None)),
            patch.object(provisioner, "_upsert_llm_connection") as mock_upsert,
            pytest.raises(ValueError, match="LITE_LLM_PROXY_PUBLIC_URL"),
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


class TestRunStep:
    """A silently dead feature cost a full debugging cycle downstream — failures must be loud."""

    @pytest.mark.asyncio
    async def test_failure_is_logged_at_error(self, caplog: pytest.LogCaptureFixture) -> None:
        async def boom() -> None:
            raise RuntimeError("upstream rejected the connection")

        with caplog.at_level(logging.ERROR):
            result = await LangfuseProvisioner._run_step("LiteLLM connection", boom())

        assert result is None
        assert any(record.levelno == logging.ERROR for record in caplog.records)
