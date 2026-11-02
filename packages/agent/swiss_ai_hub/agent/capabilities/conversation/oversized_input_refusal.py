from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import Message, RefusalReason, RefusalStopEvent
from swiss_ai_hub.core.i18n import LocaleHandler


class OversizedInputRefusal:
    """Ends a run whose input cannot fit the model with a reply rather than an error, keeping the token arithmetic to
    the thought."""

    @staticmethod
    async def refuse(
        needed: int,
        budget: int,
        model_name: str,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thought_key: str = "agent.conversation.thoughts.input_too_large",
        message_key: str = "agent.conversation.messages.input_too_large",
    ) -> RefusalStopEvent:
        """Shaped exactly like the stop event `display_llm_stream` returns for a real answer: the chunk is what the
        chat renders, and `output_messages` carries the same text for non-streaming consumers such as
        `OpenaiService`. A blueprint whose advice differs (FewShot answers from its examples, never from the file)
        passes its own keys."""
        await displayer.display_thought(t(thought_key, tokens=needed, budget=budget))
        refusal = t(message_key)
        await displayer.display_chunk(refusal, model_name=model_name)
        return RefusalStopEvent(
            reason=RefusalReason.INPUT_TOO_LARGE,
            output_messages=[Message.from_string(role="assistant", content=refusal, name=model_name)],
            chat_model_name=model_name,
        )
