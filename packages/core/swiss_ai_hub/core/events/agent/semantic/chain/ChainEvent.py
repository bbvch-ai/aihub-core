import json
from typing import Annotated, Any, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.SemanticEvent import SemanticEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class ChainEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_chain_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_chain_event.description"
    )

    metadata: Annotated[
        dict[str, Any] | None,
        Field(
            description="Metadata associated with the chain as a dictionary JSON string. "
            "For example, LangChain uses metadata to store user-defined attributes for a chain.",
        ),
    ] = None

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            SpanAttributes.METADATA: json.dumps(self.metadata),
        }
        return {k: v for k, v in attributes.items() if v is not None}
