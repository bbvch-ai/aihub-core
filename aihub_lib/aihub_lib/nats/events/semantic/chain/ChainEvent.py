import json
from typing import Any, Dict, Optional

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class ChainEvent(SemanticEvent):
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata associated with the chain as a dictionary JSON string. "
        "For example, LangChain uses metadata to store user-defined attributes for a chain.",
    )

    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            SpanAttributes.METADATA: json.dumps(self.metadata),
        }
        return {k: v for k, v in attributes.items() if v is not None}
