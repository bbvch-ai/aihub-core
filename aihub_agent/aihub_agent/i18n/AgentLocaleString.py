from typing import Self

from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler


class AgentLocaleString(LocaleString):
    """LocaleString subclass that uses AgentLocaleHandler for translation resolution.

    Use this class for i18n paths that reference agent translations (agent.*.*)
    instead of the base LocaleString.from_i18n_path().
    """

    @classmethod
    def from_i18n_path(cls, path: str) -> Self:
        """Create an AgentLocaleString from an i18n translation path."""
        return cls(
            de=AgentLocaleHandler("de")(path),
            en=AgentLocaleHandler("en")(path),
            fr=AgentLocaleHandler("fr")(path),
            it=AgentLocaleHandler("it")(path),
        )
