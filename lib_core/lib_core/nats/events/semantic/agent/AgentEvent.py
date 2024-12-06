from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from lib_core.nats.events.semantic import SemanticEvent


class AgentEvent(SemanticEvent):

    def to_semantic_convention(self) -> dict:
        return {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
        }
