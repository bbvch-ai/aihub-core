from typing import Self

from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.sysadmin_api.i18n.sysadmin_locale_handler import SysadminApiLocaleHandler


class SysadminApiLocaleString(LocaleString):
    """LocaleString that resolves the BSL ``sysadmin.*`` translation scope.

    Use this for i18n paths owned by the sysadmin plane (``sysadmin.*.*``).
    Mirrors ``ApiLocaleString`` but loads from this package's own translations
    so no BSL string ever resides in the Apache-2.0 ``packages/api``.
    """

    @classmethod
    def from_i18n_path(cls, path: str) -> Self:
        return cls(
            de=SysadminApiLocaleHandler("de")(path),
            en=SysadminApiLocaleHandler("en")(path),
            fr=SysadminApiLocaleHandler("fr")(path),
            it=SysadminApiLocaleHandler("it")(path),
        )
