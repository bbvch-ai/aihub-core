import os
from pathlib import Path
from typing import Any, Dict

import yaml

from lib_core.entities.MultiLocale import MultiLocale


class LocaleHandler:
    DEFAULT_LOCALE = "de"
    LOCALE_WHITE_LIST = ["de", "en", "fr", "it"]

    def __init__(self, locale):
        self.locale = locale  # TODO: why do we set this and never use it?

    @staticmethod
    def extract(
        locale_data: Dict[str, Any] | MultiLocale, locale: str | None = None
    ) -> Any:
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
        if locale is None or locale not in LocaleHandler.LOCALE_WHITE_LIST:
            locale = LocaleHandler.DEFAULT_LOCALE

        if isinstance(locale_data, dict):
            if len(locale_data) == 0:
                return None
            return LocaleHandler.extract_dict(locale_data, locale)
        elif isinstance(locale_data, MultiLocale):
            return LocaleHandler.extract_multi_locale(locale_data, locale)
        return locale_data

    @staticmethod
    def extract_dict(
        locale_data: Dict[str, Any] | MultiLocale, locale: str | None = None
    ):
        value = locale_data.get(locale, None)
        if value:
            return value
        fallback_value = locale_data.get(LocaleHandler.DEFAULT_LOCALE, None)
        if fallback_value:
            return fallback_value
        available_locales = list(locale_data.keys())
        if available_locales:
            return locale_data[available_locales[0]]
        raise ValueError("No language keys available")

    @staticmethod
    def extract_multi_locale(
        locale_data: Dict[str, Any] | MultiLocale, locale: str | None = None
    ):
        value = getattr(locale_data, locale, None)
        if value:
            return value
        fallback_value = getattr(locale_data, LocaleHandler.DEFAULT_LOCALE, None)
        if fallback_value:
            return fallback_value
        available_locales = [
            field
            for field in LocaleHandler.LOCALE_WHITE_LIST
            if getattr(locale_data, field, None) is not None
        ]
        if available_locales:
            return getattr(locale_data, available_locales[0])
        raise ValueError("No language keys available")

    @staticmethod
    def t_object(key: str, locale: str) -> Any:
        folder, filename, *path = key.split(".")
        current_file_directory = Path(__file__).resolve().parent
        app_directory = current_file_directory.parent
        src_directory = app_directory.parent
        lang_directory = os.path.join(src_directory, "lang", folder)
        file_path = os.path.join(lang_directory, f"{filename}.{locale}.yml")

        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            for key in path:
                data = data[key]
            return data
