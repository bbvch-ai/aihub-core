from typing import ClassVar, Dict

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class GuardEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_guard_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_guard_event.description"
    )

    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.GUARDRAIL.value,
        }

        return {k: v for k, v in attributes.items() if v is not None}
