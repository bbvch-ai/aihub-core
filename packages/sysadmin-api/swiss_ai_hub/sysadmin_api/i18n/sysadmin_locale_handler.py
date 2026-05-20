# SPDX-License-Identifier: LicenseRef-Proprietary
import os

from swiss_ai_hub.core.i18n import LocaleHandler


class SysadminApiLocaleHandler(LocaleHandler):
    """Adds sysadmin-api's own ``translations`` directory to the i18n load path."""

    def get_locale_paths(self) -> list[str]:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.join(current_file_directory, "translations")

        return [*super().get_locale_paths(), relative_path]
