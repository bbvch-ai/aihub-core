"""Tests for LangfuseProvisioner — Langfuse auto-provisioning on API startup."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from aihub_lib.infrastructure.langfuse.LangfuseProvisioner import (
    LangfuseProvisioner,
)


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
    with (
        patch(
            "aihub_lib.infrastructure.langfuse.LangfuseProvisioner.LangfuseSettings",
            return_value=mock_langfuse_settings,
        ),
        patch("aihub_lib.infrastructure.langfuse.LangfuseProvisioner.LiteLLMProxySettings"),
    ):
        return LangfuseProvisioner()


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
    async def test_provision_raises_on_step_failure(self, provisioner: LangfuseProvisioner) -> None:
        with (
            patch.object(provisioner, "_fetch_litellm_models", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await provisioner.provision()


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
                "model_name": "text-generation/gpt-oss-120b",
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
            {"model_name": "text-generation/gpt-oss-120b", "model_info": {}},
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
