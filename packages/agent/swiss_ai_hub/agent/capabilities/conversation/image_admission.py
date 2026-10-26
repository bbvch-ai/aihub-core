from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import Message, RefusalReason, RefusalStopEvent
from swiss_ai_hub.core.generative_ai import ImageBudget, LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler


class ImageAdmission:
    """Decides which images of a turn reach the model, before anything is spent on the turn.

    Earlier turns give their images up silently, since chat clients resend them on every turn and they were
    answered already; the last turn is what is being asked, so an image there that cannot be sent ends the run
    with a reply naming why, rather than an answer that ignores it or a provider error.
    """

    @staticmethod
    async def admit(
        history: list[ChatMessage], llm: LLMConfig, displayer: EventDisplayer, t: LocaleHandler
    ) -> list[ChatMessage] | RefusalStopEvent:
        """`history` with the images the model may receive, or the refusal when the last turn exceeds that."""
        if ImageBudget.count(history) == 0:
            return history

        last_turn_images = ImageBudget.count(history[-1:])
        if not ImageAdmission._accepts_images(llm):
            if last_turn_images:
                return await ImageAdmission._refuse(
                    RefusalReason.IMAGES_NOT_ACCEPTED, "images_not_accepted", last_turn_images, None, llm, displayer, t
                )
            return ImageBudget.without_images(history)

        max_images = llm.max_images
        if max_images is None:
            return history
        if last_turn_images > max_images:
            return await ImageAdmission._refuse(
                RefusalReason.TOO_MANY_IMAGES, "too_many_images", last_turn_images, max_images, llm, displayer, t
            )
        return ImageBudget.fit(history, max_images)

    @staticmethod
    def _accepts_images(llm: LLMConfig) -> bool:
        """Off by the profile, or by a model that declares it cannot read images; an undeclared model is given the
        benefit of the doubt, since LiteLLM leaves `supports_vision` unset for most models."""
        return llm.default_parameter.accept_images is True and llm.supports_vision is not False

    @staticmethod
    async def _refuse(
        reason: RefusalReason,
        key: str,
        images: int,
        max_images: int | None,
        llm: LLMConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RefusalStopEvent:
        """Shaped like `OversizedInputRefusal.refuse`: the chunk is what the chat renders, `output_messages` the same
        text for non-streaming consumers."""
        model_name = str(llm.model_name)
        await displayer.display_thought(
            t(f"agent.conversation.thoughts.{key}", images=images, max_images=max_images, model=model_name)
        )
        refusal = t(f"agent.conversation.messages.{key}", images=images, max_images=max_images)
        await displayer.display_chunk(refusal, model_name=model_name)
        return RefusalStopEvent(
            reason=reason,
            output_messages=[Message.from_string(role="assistant", content=refusal, name=model_name)],
            chat_model_name=model_name,
        )
