from functools import cache
from typing import Annotated, Any

from swiss_ai_hub.core.agents import AgentConfig, StepConfig
from swiss_ai_hub.core.form import SecretFieldWalker
from swiss_ai_hub.core.secrets import SecretEncryptionService, SecretPathTransformer

from swiss_ai_hub.agent.mcp.mcp_auth_resolver import McpAuthResolver

_USER_TOKEN_PATH = f"data.{McpAuthResolver.AIHUB_HEADERS_KEY}.{McpAuthResolver.USER_TOKEN_HEADER}"


class TraceInputRedactor:
    """
    Masks secrets in step inputs before they become span attributes.

    Step spans are exported to Langfuse and the cloud trace backend, so a config's API key or the forwarded user token
    would otherwise be readable by anyone who can open a trace. Which config fields are secret follows from the
    announced form, as it does for encryption at rest; an empty secret stays empty so an unset one remains visible.
    """

    @classmethod
    def config(cls, config: Annotated[AgentConfig | StepConfig, "Config passed to a step"]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config.model_dump(), set(cls._secret_paths(type(config))), cls._mask)

    @classmethod
    def context(
        cls, serialized: Annotated[dict[str, Any], "A context as BaseContext.to_serializable returns it"]
    ) -> dict[str, Any]:
        """The dispatcher keeps the forwarded X-AIHub-* headers in RunContext; only the user token among them is
        secret, the others (such as the anonymisation flag) help when reading a trace. It also keeps the profile's
        config there with its secrets still encrypted, and ciphertext is a secret too once the key leaks."""
        return cls._without_ciphertext(SecretPathTransformer.transform(serialized, {_USER_TOKEN_PATH}, cls._mask))

    @classmethod
    def _without_ciphertext(cls, node: Any) -> Any:
        if isinstance(node, dict):
            return {key: cls._without_ciphertext(value) for key, value in node.items()}
        if isinstance(node, list):
            return [cls._without_ciphertext(item) for item in node]
        return SecretEncryptionService.MASK if SecretEncryptionService.is_encrypted(node) else node

    @staticmethod
    @cache
    def _secret_paths(config_class: type[AgentConfig | StepConfig]) -> frozenset[str]:
        """Only a config with a form of its own can announce a secret. AgentConfig's base form holds none, and building
        it for a subclass that does not override it fails on the subclass's required fields."""
        as_form = getattr(config_class, "as_form", None)
        if as_form is None or as_form.__func__ is AgentConfig.as_form.__func__:
            return frozenset()
        return frozenset(SecretFieldWalker.secret_paths(as_form().to_formkit_form()))

    @staticmethod
    def _mask(value: Any) -> Any:
        if value is None or value == "":
            return value
        return SecretEncryptionService.MASK
