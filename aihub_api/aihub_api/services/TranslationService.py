import json
import logging

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from llama_index.core import PromptTemplate
from llama_index.llms.openai_like import OpenAILike

logger = logging.getLogger(__name__)

LOCALE_NAMES = {"en": "English", "de": "German", "fr": "French", "it": "Italian"}


class TranslationService:
    """
    Service for automatically translating content to all supported locales using a single LLM call.
    """

    @classmethod
    async def translate(
        cls, locale_string: LocaleString, llm_config: LLMConfig, t: LocaleHandler, source_locale: str = "en"
    ) -> LocaleString:
        """
        Translates fields in a translatable object (LocaleString).
        """
        source_text = locale_string.in_locale(source_locale)
        target_locales = [locale for locale in t.supported_locales if locale != source_locale]
        new_translations = await cls._get_translations_from_llm(
            text=source_text,
            source_language_code=source_locale,
            target_language_codes=target_locales,
            llm=llm_config.to_llama_index()[0],
            t=t,
        )
        final_data = locale_string.model_dump()
        new_data = new_translations.model_dump(exclude_unset=True)
        final_data.update(new_data)
        return LocaleString(**final_data)

    @classmethod
    async def _get_translations_from_llm(
        cls, text: str, source_language_code: str, target_language_codes: list[str], llm: OpenAILike, t: LocaleHandler
    ) -> LocaleString:
        target_languages = ", ".join([t(f"api.common.translation.{lang}") for lang in target_language_codes])
        prompt = PromptTemplate(t("api.common.translation.prompt"))
        response = await llm.apredict(
            prompt,
            source_language=t(f"api.common.translation.{source_language_code}"),
            target_languages=target_languages,
            locale_codes=target_language_codes,
            text=text,
        )
        translations = json.loads(response)
        return LocaleString(**translations)
