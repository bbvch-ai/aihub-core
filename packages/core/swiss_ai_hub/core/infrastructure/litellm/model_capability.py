from enum import StrEnum


class ModelCapability(StrEnum):
    """Something a model picker may require of a chat model, read from the LiteLLM `supports_*` flag it names."""

    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    REASONING = "reasoning"

    @property
    def model_info_key(self) -> str:
        match self:
            case ModelCapability.VISION:
                return "supports_vision"
            case ModelCapability.TOOL_CALLING:
                return "supports_function_calling"
            case ModelCapability.STRUCTURED_OUTPUT:
                return "supports_response_schema"
            case ModelCapability.REASONING:
                return "supports_reasoning"
