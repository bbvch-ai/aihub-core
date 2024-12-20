from typing import Dict

from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class AgentEvent(SemanticEvent):
    def to_semantic_convention(self) -> Dict[str, str]:
        return {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
        }
