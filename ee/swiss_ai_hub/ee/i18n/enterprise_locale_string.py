from typing import Self

from swiss_ai_hub.agent import AgentLocaleString

from swiss_ai_hub.ee.i18n.enterprise_locale_handler import EnterpriseLocaleHandler


class EnterpriseLocaleString(AgentLocaleString):
    """AgentLocaleString that also finds the translations shipped with the enterprise package."""

    @classmethod
    def from_i18n_path(cls, path: str) -> Self:
        return cls(
            de=EnterpriseLocaleHandler("de")(path),
            en=EnterpriseLocaleHandler("en")(path),
            fr=EnterpriseLocaleHandler("fr")(path),
            it=EnterpriseLocaleHandler("it")(path),
        )
