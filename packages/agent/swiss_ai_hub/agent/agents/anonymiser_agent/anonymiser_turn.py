import re
from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ConversationTitleEvent, LLMStopEvent, Message
from swiss_ai_hub.core.generative_ai import AnonymisationVocabulary, PlaceholderMap
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import PresidioAnalyzerClient

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import TITLE_GENERATED_KEY


class AnonymiserTurn:
    """One message to the anonymiser: anonymised, or restored when it carries placeholders this chat issued.

    The placeholder map lives in the thread context, so a chat restores only what it anonymised itself and a new
    chat starts empty. The title is fixed, because a title drawn from the message would put the personal data in
    the chat list. Nothing here calls a model: the text goes to the deployment's analyzer only.
    """

    PLACEHOLDER_MAP_KEY: ClassVar[str] = "anonymiser_placeholder_map"
    SOURCE_NAME: ClassVar[str] = "presidio-analyzer"
    BACKTICK_RUN: ClassVar[re.Pattern[str]] = re.compile(r"`+")
    # A rule line (`---`, `===`) directly under text, with no blank line between them.
    RULE_UNDER_TEXT: ClassVar[re.Pattern[str]] = re.compile(r"(?m)(?<=\S)\n(?=[ ]{0,3}(?:-{3,}|={3,})[ \t]*$)")

    @classmethod
    async def answer(
        cls,
        text: str,
        analyzer: PresidioAnalyzerClient,
        displayer: EventDisplayer,
        thread_context: ThreadContext,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        await cls._name_the_chat(displayer, thread_context, t)
        placeholders = PlaceholderMap.model_validate(await thread_context.get(cls.PLACEHOLDER_MAP_KEY, {}))
        unknown = placeholders.unknown_in(text)
        if not text.strip():
            reply = t("agent.anonymiser_agent.messages.empty")
        elif placeholders.issued_in(text):
            reply = f"{t('agent.anonymiser_agent.messages.restored')}\n\n{cls.readable(placeholders.restore(text))}"
        else:
            reply = await cls._anonymised_reply(text, placeholders, analyzer, displayer, t)
            await thread_context.set(cls.PLACEHOLDER_MAP_KEY, placeholders.model_dump())
        if unknown:
            listed = ", ".join(f"`{token}`" for token in unknown)
            reply += f"\n\n{t('agent.anonymiser_agent.messages.unknown_placeholders', placeholders=listed)}"
        await displayer.display_chunk(reply, model_name=cls.SOURCE_NAME)
        return LLMStopEvent(output_messages=[Message.from_string(role="assistant", content=reply)])

    @classmethod
    async def _anonymised_reply(
        cls,
        text: str,
        placeholders: PlaceholderMap,
        analyzer: PresidioAnalyzerClient,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> str:
        await displayer.display_thought(t("agent.anonymiser_agent.thoughts.anonymising"))
        spans = await analyzer.analyze(
            text, AnonymisationVocabulary.ENTITIES, AnonymisationVocabulary.allow_list_pattern()
        )
        masked = placeholders.mask(text, spans)
        if masked == text:
            return t("agent.anonymiser_agent.messages.nothing_found")
        return f"{t('agent.anonymiser_agent.messages.anonymised')}\n\n{cls.code_block(masked)}"

    @classmethod
    async def _name_the_chat(cls, displayer: EventDisplayer, thread_context: ThreadContext, t: LocaleHandler) -> None:
        if await thread_context.get(TITLE_GENERATED_KEY):
            return
        await displayer.display_event(ConversationTitleEvent(title=t("agent.anonymiser_agent.title")))
        await thread_context.set(TITLE_GENERATED_KEY, True)

    @classmethod
    def readable(cls, text: str) -> str:
        """A pasted answer often lost its blank lines on the way (chat copy buttons drop them), and then a `---`
        separator right under a line turns that line into a heading. A blank line before it keeps it a separator."""
        return cls.RULE_UNDER_TEXT.sub("\n\n", text.replace("\r\n", "\n"))

    @classmethod
    def code_block(cls, text: str) -> str:
        """The anonymised text goes in a fenced block, which the chat shows verbatim with its own copy button, so what
        the user takes elsewhere is exactly the text with placeholders; a restored answer is read, so it stays
        markdown. The fence outgrows any backtick run in the text, so a pasted code block cannot close it."""
        longest = max((len(run) for run in cls.BACKTICK_RUN.findall(text)), default=0)
        fence = "`" * max(3, longest + 1)
        return f"{fence}text\n{text}\n{fence}"
