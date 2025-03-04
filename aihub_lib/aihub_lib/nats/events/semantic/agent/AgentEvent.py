from typing import Dict

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class AgentEvent(SemanticEvent):
    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
        }
        return {k: v for k, v in attributes.items() if v is not None}
