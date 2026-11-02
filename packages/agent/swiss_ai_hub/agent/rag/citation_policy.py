from swiss_ai_hub.core.events.agent import RAGStartEvent, UserMessageEvent


class CitationPolicy:
    """Whether a RAG run asks the model for inline citations, decided once for every prompt part that asks."""

    @staticmethod
    def cites_sources(start_event: UserMessageEvent | RAGStartEvent) -> bool:
        """A chat always cites; a programmatic caller rendering the answer without a source list opts out."""
        return not isinstance(start_event, RAGStartEvent) or start_event.cite_sources
