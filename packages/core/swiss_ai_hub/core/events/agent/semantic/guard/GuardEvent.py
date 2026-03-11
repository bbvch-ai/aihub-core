from typing import ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from swiss_ai_hub.core.events.agent.semantic.SemanticEvent import SemanticEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class GuardEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_guard_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_guard_event.description"
    )

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.GUARDRAIL.value,
        }

        return {k: v for k, v in attributes.items() if v is not None}
