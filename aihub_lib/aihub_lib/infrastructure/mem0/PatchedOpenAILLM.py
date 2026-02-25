import logging
from typing import Self, override

from mem0.llms.openai import OpenAILLM

logger = logging.getLogger(__name__)


class PatchedOpenAILLM(OpenAILLM):
    """
    Patches mem0's OpenAILLM to strip unsupported response_format types.

    Some providers (e.g. Infomaniak / Swiss LLM Cloud) no longer accept
    response_format={"type": "json_object"} and require json_schema instead.
    mem0 hardcodes json_object in its vector store add path, so this patch
    removes it and relies on the prompt to produce valid JSON.
    """

    @classmethod
    def from_llm(cls, llm: OpenAILLM) -> Self:
        """Wrap an existing OpenAILLM instance, preserving its config and client."""
        instance = cls.__new__(cls)
        instance.config = llm.config
        instance.client = llm.client
        return instance

    @override
    def generate_response(
        self,
        messages,
        response_format=None,
        tools=None,
        tool_choice="auto",
        **kwargs,
    ):
        if response_format and isinstance(response_format, dict) and response_format.get("type") == "json_object":
            logger.debug("Stripping response_format={'type': 'json_object'} — unsupported by provider.")
            response_format = None

        return super().generate_response(
            messages=messages,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )
