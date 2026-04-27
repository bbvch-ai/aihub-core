from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RAGStopEvent(StopEvent):
    """Stop event emitted by RAG-style agents.

    Carries a `context_sufficient` flag so a parent agent (e.g. via `AgentInTheLoop`) can
    branch on whether the RAG run produced an answer grounded in retrieved context, or
    whether the LLM was forced to respond with an "I don't know"-style fallback.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_stop_event.description")

    context_sufficient: Annotated[
        bool,
        Field(
            description=(
                "Whether the retrieved context was sufficient to ground the answer. "
                "True covers three cases: (a) the sufficiency guard ran and accepted the "
                "context, (b) the guard was disabled via `check_context_sufficiency=False`, "
                "or (c) the guard step was never reached on this run. "
                "False means the guard ran, exhausted all retrieval hops, and judged the "
                "final context insufficient — so the LLM was forced to produce an "
                '"I don\'t know"-style fallback answer.'
            )
        ),
    ] = True
