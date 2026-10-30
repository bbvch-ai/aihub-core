from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from openai.types.create_embedding_response import Usage
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"


async def _embed(vector: list[float] | str, encoding_format: str):
    upstream = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=vector)], usage=Usage(prompt_tokens=4, total_tokens=4)
    )
    client = Mock(embeddings=Mock(create=AsyncMock(return_value=upstream)))
    with (
        patch.object(OpenaiService, "_assert_model_access"),
        patch.object(OpenaiService, "_model_names_by_type", new=AsyncMock(return_value=["embedding/bge-m3"])),
        patch(f"{_SERVICE}.LiteLLMService.openai_aclient_for_user", new=AsyncMock(return_value=client)),
    ):
        return await OpenaiService.get_embeddings(
            model_name="embedding/bge-m3", input_text="hello", user=fake_user(), encoding_format=encoding_format
        )


@pytest.mark.asyncio
async def test_embeddings_follow_openais_object_and_report_usage():
    response = (await _embed([0.1, 0.2], "float")).model_dump()

    assert response["data"][0]["object"] == "embedding"
    assert response["data"][0]["embedding"] == [0.1, 0.2]
    assert response["usage"] == {"prompt_tokens": 4, "total_tokens": 4}


@pytest.mark.asyncio
async def test_base64_embeddings_are_returned_as_sent():
    response = await _embed("zczMPc3MTD4=", "base64")
    assert response.data[0].embedding == "zczMPc3MTD4="
