import json
from typing import Optional, Dict

from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues
from pydantic import Field

from lib_core.nats.events.semantic import SemanticEvent


class ChainEvent(SemanticEvent):
    metadata: Optional[Dict] = Field(
        None,
        description="Metadata associated with the chain as a dictionary JSON string. "
                    "For example, LangChain uses metadata to store user-defined attributes for a chain."
    )

    def to_semantic_convention(self) -> dict:
        return {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            SpanAttributes.METADATA: json.dumps(self.metadata),
        }
