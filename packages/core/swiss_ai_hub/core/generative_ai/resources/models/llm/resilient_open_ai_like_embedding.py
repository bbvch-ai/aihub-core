from typing import Annotated, Any, override

import httpx
from llama_index.embeddings.openai_like import OpenAILikeEmbedding
from pydantic import Field


class ResilientOpenAILikeEmbedding(OpenAILikeEmbedding):
    """
    OpenAILikeEmbedding whose connect fails fast and whose clients its owner closes.

    The embedding counterpart of ``ResilientOpenAILike``; its ``_get_credential_kwargs`` and ``aclose`` say why.
    """

    connect_timeout: Annotated[float, Field(description="Seconds allowed to open the connection to the gateway.")]

    @override
    def _get_credential_kwargs(self, is_async: bool = False) -> dict[str, Any]:
        return {
            **super()._get_credential_kwargs(is_async=is_async),
            "timeout": httpx.Timeout(self.timeout, connect=self.connect_timeout),
        }

    async def aclose(self) -> None:
        if self._aclient is not None:
            await self._aclient.close()
        if self._client is not None:
            self._client.close()
