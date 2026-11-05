from typing import ClassVar

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.generative_ai import GatewayGuardrails
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.context.run.run_context import RunContext


class RunAnonymisation:
    """Whether a run anonymises its LLM calls: its profile's toggle is on, or the run that delegated to it did.

    A delegated run answers for the delegating one, so it inherits the anonymisation through a header on its start
    event. The header comes over the same path as the client's `X-AIHub-*` headers and is just as untrusted, which
    is why it can only switch anonymisation on: a run is never anonymised less than its own profile says.
    """

    HEADER: ClassVar[str] = "X-AIHub-Anonymise"
    # Underscore-prefixed like the dispatcher's other keys, so no StartEvent field can overwrite it.
    _INHERITED_KEY: ClassVar[str] = "_inherited_anonymise"

    @classmethod
    async def remember_inherited(cls, event: StartEvent, run_context: RunContext) -> bool:
        """Keep the delegating run's anonymisation for the whole run; later events carry the client's headers."""
        inherited = (event._aihub_headers or {}).get(cls.HEADER.lower()) == "true"
        if inherited:
            await run_context.set(cls._INHERITED_KEY, True)
        return inherited

    @classmethod
    async def requested_guardrails(cls, agent_config: AgentConfig, run_context: RunContext) -> tuple[str, ...]:
        anonymise = agent_config.anonymise is True or await run_context.get(cls._INHERITED_KEY, False)
        return (GatewayGuardrails.PII_ANONYMISATION,) if anonymise else ()

    @classmethod
    def delegation_headers(cls) -> dict[str, str] | None:
        """Headers that make a run delegated from the current step anonymise as well."""
        return {cls.HEADER: "true"} if GatewayGuardrails.anonymising() else None

    @staticmethod
    async def show_notice(displayer: EventDisplayer, t: LocaleHandler) -> None:
        """Say so at the top of the answer. A chunk, like the tool loop's notice, so every chat client shows it."""
        await displayer.display_chunk(f"_{t('agent.base_agent.notice.anonymised')}_\n\n", "")
