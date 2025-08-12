import json
import logging
from typing import TypeVar

from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import (
    ChatLLMConfig,
    ChatLLMParameter,
)
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from llama_index.core.base.llms.types import ChatMessage, MessageRole

logger = logging.getLogger(__name__)

T = TypeVar("T", LocaleStringEntity, LocaleString)

LOCALE_NAMES = {"en": "English", "de": "German", "fr": "French", "it": "Italian"}


class TranslationService:
    """
    Service for automatically translating content to all supported locales using a single, efficient LLM call.
    """

    @classmethod
    async def translate(
        cls, translatable: T, llm_config: ChatLLMConfig, t: LocaleHandler, source_locale: str = "en"
    ) -> T:
        """
        Translates missing fields in a translatable object (LocaleString or LocaleStringEntity).
        """
        if not translatable:
            return translatable

        source_text = getattr(translatable, source_locale, None)
        if not source_text:
            return translatable

        missing_locales = [
            locale
            for locale in t.supported_locales
            if locale != source_locale and not getattr(translatable, locale, None)
        ]

        if not missing_locales:
            return translatable

        translations = await cls._get_translations_from_llm(
            text=source_text,
            source_locale=source_locale,
            target_locales=missing_locales,
            llm_config=llm_config,
        )

        if isinstance(translatable, LocaleStringEntity):
            for locale, translation in translations.items():
                if translation:
                    setattr(translatable, locale, translation)
            return translatable
        elif isinstance(translatable, LocaleString):
            existing_data = translatable.model_dump()
            existing_data.update(translations)
            return LocaleString(**existing_data)

        return translatable

    @classmethod
    async def _get_translations_from_llm(
        cls, text: str, source_locale: str, target_locales: list[str], llm_config: ChatLLMConfig
    ) -> dict[str, str]:
        if not target_locales:
            return {}

        source_language = LOCALE_NAMES.get(source_locale, source_locale)
        target_languages = ", ".join([LOCALE_NAMES.get(locale, locale) for locale in target_locales])

        system_prompt = (
            "You are a professional and precise translator. "
            f"Translate the given text from {source_language} into the following languages: {target_languages}. "
            "Your response must be a single, valid JSON object. The keys should be the two-letter "
            f"locale codes ({', '.join(target_locales)}), and the values should be the translated strings. "
            "Do not include any other text, explanations, or markdown."
        )

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=text),
        ]

        llm, _ = llm_config.to_llama_index(
            ChatLLMParameter(
                temperature=0.0,
                max_tokens=1024,
            )
        )
        if hasattr(llm.llm, "response_format"):
            llm.llm.response_format = {"type": "json_object"}

        response = await llm.achat(messages)
        content = response.message.content.strip()
        return json.loads(content)
