from typing import ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.semantic.SemanticEvent import SemanticEvent


class AgentEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_agent_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_agent_event.description"
    )

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
        }
        return {k: v for k, v in attributes.items() if v is not None}
