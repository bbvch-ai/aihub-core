from typing import ClassVar, Self

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString


class MemoryWriterAgentConfig(AgentConfig):
    """
    Config for the system `MemoryWriterAgent`.

    Its identity is **baked as non-configurable primitives** (not FormKit elements): the writer is a system
    agent triggered programmatically, never configured via the Admin UI, so there is no `agent_configs`
    profile record for it. Because these values are non-configurable, `get_non_configurable_values()` supplies
    them and `deep_merge(non_configurable, {})` yields a valid config even when the RPC returns an empty
    config — so the run starts with no seeded DB record. The mem0 LLM/embedding models come from
    `MEM0_*` settings, so no LLM field is needed here.
    """

    AGENT_CLASS: ClassVar[str] = "MemoryWriterAgent"
    AGENT_ID: ClassVar[str] = "memory-writer"

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            agent_id=cls.AGENT_ID,
            name=LocaleString(
                de="Speicher-Writer", en="Memory Writer", fr="Rédacteur de mémoire", it="Registratore di memoria"
            ),
            description=LocaleString(
                de="Systemagent, der Nutzerspeicher ausserhalb des kritischen Pfads persistiert.",
                en="System agent that persists user memory off the chat critical path.",
                fr="Agent système qui persiste la mémoire utilisateur hors du chemin critique.",
                it="Agente di sistema che persiste la memoria utente fuori dal percorso critico.",
            ),
            icon="mdi:content-save",
        )
