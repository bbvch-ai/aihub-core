from swiss_ai_hub.core.events.agent import NotAMetaQuestionEvent, UserMessageEvent


def check_passed_meta_question_gate(start_event: object, clear: NotAMetaQuestionEvent | None) -> bool:
    """
    Gate that holds back the normal entry steps until meta-question detection has cleared a chat
    message. Only chat (`UserMessageEvent`) entries are gated; programmatic starts (e.g. `RAGStartEvent`)
    skip detection entirely and proceed immediately.

    Lives in the self-awareness package (not `rag`) so any agent can gate its entry steps without
    importing the heavy `rag` package, which would create an import cycle.
    """
    return clear is not None or not isinstance(start_event, UserMessageEvent)
