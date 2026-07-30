import logging
import os
from typing import Any

import i18n
import yaml

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

logger = logging.getLogger(__name__)


class LocaleHandler:
    DEFAULT_LOCALE = "de"
    LOCALE_WHITE_LIST = ["de", "en", "fr", "it"]

    def __init__(self, locale: str | None = None, locale_paths: list[str] | None = None):
        self._locale = locale or self.DEFAULT_LOCALE

        i18n.set("skip_locale_root_data", True)
        i18n.set("enable_memoization", True)

        i18n_load_path = i18n.config.get("load_path").copy()
        locale_paths = locale_paths or []
        for path in set(locale_paths + self.get_locale_paths()):
            i18n_load_path.append(path)

        i18n.config.set("load_path", list(set(i18n_load_path)))

    @property
    def locale(self):
        return self._locale

    @property
    def supported_locales(self):
        return self.LOCALE_WHITE_LIST

    def get_locale_paths(self) -> list[str]:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.join(current_file_directory, "translations")
        return [relative_path]

    def get_locale(self, locale: str):
        if locale and locale in self.LOCALE_WHITE_LIST:
            return locale
        return self._locale or self.DEFAULT_LOCALE

    def extract(self, locale_data: dict[str, Any] | LocaleString, locale: str | None = None) -> Any:
        """
        Some database properties are multi-lingual. This function returns the property in the user's locale.
        Example:
        agent_name = {
            "en": "Search-Agent",
            "de": "Such-Agent",
            "fr": "Agent de recherche",
            "it": "Agente di ricerca"
        }
        -> extract(agent_name) -> "Such-Agent" (if the user's locale is "de")
        """
        locale = self.get_locale(locale)
        if isinstance(locale_data, dict):
            if len(locale_data) == 0:
                return None
            return self.extract_dict(locale_data, locale)
        elif isinstance(locale_data, LocaleString | LocaleStringEntity):
            return self.extract_multi_locale(locale_data, locale)
        return locale_data

    def extract_dict(self, locale_data: dict[str, Any] | LocaleString, locale: str) -> Any:
        locale = self.get_locale(locale)
        value = locale_data.get(locale, None)
        if value:
            return value
        fallback_value = locale_data.get(self.DEFAULT_LOCALE, None)
        if fallback_value:
            return fallback_value
        available_locales = list(locale_data.keys())
        if available_locales:
            return locale_data[available_locales[0]]
        return None

    def extract_multi_locale(self, locale_data: dict[str, Any] | LocaleString, locale: str | None = None) -> Any:
        locale = self.get_locale(locale)
        value = getattr(locale_data, locale, None)
        if value:
            return value
        fallback_value = getattr(locale_data, self.DEFAULT_LOCALE, None)
        if fallback_value:
            return fallback_value
        available_locales = [field for field in self.LOCALE_WHITE_LIST if getattr(locale_data, field, None)]
        if available_locales:
            return getattr(locale_data, available_locales[0])
        return None

    def t_object(self, key: str, locale: str | None = None) -> Any:
        locale = self.get_locale(locale)
        folder, filename, *path = key.split(".")
        folder_paths = i18n.config.get("load_path")
        for folder_path in folder_paths:
            potential_file_path = os.path.join(folder_path, folder, f"{filename}.{locale}.yml")
            if not os.path.isfile(potential_file_path):
                continue
            with open(potential_file_path) as file:
                data = yaml.safe_load(file)
                for key in path:
                    data = data[key]
                return data

        raise FileNotFoundError(f"Unable to extract t_object {filename}.{locale}.yml")

    def in_locale(self, locale: str):
        return self.__class__(
            locale=locale,
        )

    def __call__(self, key: str, locale: str | None = None, **kwargs) -> str:
        return i18n.t(key, locale=self.get_locale(locale), **kwargs)
