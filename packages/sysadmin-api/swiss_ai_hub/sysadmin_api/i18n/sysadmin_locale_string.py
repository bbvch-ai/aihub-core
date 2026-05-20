# SPDX-License-Identifier: LicenseRef-Proprietary
from typing import Self

from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.sysadmin_api.i18n.sysadmin_locale_handler import SysadminApiLocaleHandler


class SysadminApiLocaleString(LocaleString):
    """LocaleString that resolves the ``sysadmin.*`` translation scope."""

    @classmethod
    def from_i18n_path(cls, path: str) -> Self:
        return cls(
            de=SysadminApiLocaleHandler("de")(path),
            en=SysadminApiLocaleHandler("en")(path),
            fr=SysadminApiLocaleHandler("fr")(path),
            it=SysadminApiLocaleHandler("it")(path),
        )
