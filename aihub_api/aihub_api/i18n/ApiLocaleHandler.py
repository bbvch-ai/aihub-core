import os
from typing import List

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class ApiLocaleHandler(LocaleHandler):
    def get_locale_paths(self) -> List[str]:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.join(current_file_directory, "translations")

        return [*super().get_locale_paths(), relative_path]
