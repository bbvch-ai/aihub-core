from typing import Any

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent


class SemanticEvent(ControlAndDisplayEvent):
    """
    A base class for events that must report their data to an OpenInference-compatible tracing system,
    such as Langfuse. By inheriting from both `ControlEvent` and `DisplayEvent`, `SemanticEvent`:
    - Influences workflow execution and can control the system flow (like any `ControlEvent`).
    - Remains visible to the end-user or UI (like any `DisplayEvent`).
    - Introduces the requirement to define a `to_semantic_convention()` method,
      providing structured semantic attributes for OpenInference tracing.

    ### Why SemanticEvent?
    The primary purpose is to provide a flexible foundation for events that carry semantically rich
    information which should be recorded in tracing and observability tools. By encouraging a
    `to_semantic_convention()` method, `SemanticEvent` standardizes the process of converting event
    data into a form suitable for advanced analytics, debugging, and telemetry.

    ### Integrating with OpenInference
    OpenInference mandates a set of semantic conventions for attributes, ensuring that tooling
    (like Langfuse) can interpret and visualize LLM application behavior. Subclasses of
    `SemanticEvent` should implement `to_semantic_convention()` to:
    - Flatten nested structures into simple key-value pairs following the OpenInference attribute schema.
    - Use reserved attribute names (e.g. `llm.model_name`, `document.id`) as defined in the specification.

    This allows downstream systems to understand and correlate complex operations like retrieval,
    reranking, or prompt tuning with high-level performance metrics or user outcomes.

    ### Note
    Since `to_semantic_convention()` is not implemented here, subclasses must provide their own logic
    to translate the event’s internal state into OpenInference semantic attributes.
    """

    def to_semantic_convention(self) -> dict[str, Any]:
        """
        Convert the event’s internal data into a dictionary of attributes adhering to OpenInference
        semantic conventions. This method MUST be implemented by subclasses to fulfill the
        OpenInference tracing specification.

        The returned dictionary should:
        - Flatten nested objects and lists into `attribute_name.index.key` form where needed.
        - Use reserved attribute names where possible (e.g. `llm.model_name`, `document.id`).
        - Only include simple types (`bool`, `str`, `int`, `float`) or simple lists thereof.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError
