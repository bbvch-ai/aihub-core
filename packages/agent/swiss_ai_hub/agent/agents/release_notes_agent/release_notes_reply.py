from typing import Annotated

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, LLMStopEvent, Message

from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation


class ReleaseNotesReply:
    """Ends a turn on what the chat showed, whether a changelog or a sentence saying why there is none.

    The follow-up questions are grounded on the user's question and the text in the writing language only: the whole
    history and the translations would only make that call larger, and its questions come out in one language either
    way. The run itself ends on everything shown.
    """

    @staticmethod
    def complete(
        question: Annotated[str, "What the user asked"],
        shown: Annotated[str, "Everything the chat showed, exactly as streamed"],
        model_name: Annotated[str, "Model the answer is attributed to"],
        answered: Annotated[str | None, "The part shown in the writing language; None when it is all of it"] = None,
    ) -> Conversation.CompleteRequest:
        asked = [Message.from_string(role="user", content=question)]
        answer = LLMEvent(
            input_messages=asked,
            output_messages=[Message.from_string(role="assistant", content=answered or shown, name=model_name)],
            chat_model_name=model_name,
        )
        stop = LLMStopEvent(
            input_messages=asked,
            output_messages=[Message.from_string(role="assistant", content=shown, name=model_name)],
            chat_model_name=model_name,
        )
        return Conversation.complete(answer=answer, stop=stop)

    @classmethod
    async def say(
        cls,
        text: Annotated[str, "A sentence for the user, e.g. why there is no changelog"],
        question: Annotated[str, "What the user asked"],
        displayer: Annotated[EventDisplayer, "Where the sentence is shown"],
        model_name: Annotated[str, "Model the answer is attributed to"],
    ) -> Conversation.CompleteRequest:
        """A bare stop event reaches chat clients as an empty message, so the sentence is streamed first."""
        await displayer.display_chunk(text, model_name=model_name)
        return cls.complete(question, text, model_name)
