import asyncio
import logging
import re

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import LiteLLMService, trace_fn

from swiss_ai_hub.api.routes.translation.dto.translation_outcome import TranslationOutcome
from swiss_ai_hub.api.routes.translation.dto.translation_request import TranslationRequest
from swiss_ai_hub.api.routes.translation.dto.translation_response import TranslationResponse

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for translating content into all supported locales, one concurrent LLM call per target locale.

    One call per locale keeps a single bad generation from discarding the others, and avoids wrapping
    large texts (agent system prompts) in a JSON envelope the model has to escape correctly.
    """

    DEFAULT_MODEL = "text-generation/gemma-4-31B-it"
    TRANSLATION_PATTERN = re.compile(r"<translation>(.*)</translation>", re.DOTALL)

    @classmethod
    @trace_fn
    async def translate_from_request(
        cls, request: TranslationRequest, t: LocaleHandler, user: UserIdentity
    ) -> TranslationResponse:
        """
        Translates a LocaleString from the request to all supported locales.
        """
        llm_config = LLMConfig(model_name=request.model_name or cls.DEFAULT_MODEL)
        outcome = await cls.translate(
            locale_string=request.text,
            llm_config=llm_config,
            t=t,
            source_locale=request.source_locale,
            user=user,
        )
        return TranslationResponse.from_outcome(outcome)

    @classmethod
    @trace_fn
    async def translate(
        cls,
        locale_string: LocaleString,
        llm_config: LLMConfig,
        t: LocaleHandler,
        user: UserIdentity,
        source_locale: str = "en",
    ) -> TranslationOutcome:
        """
        Translates the source locale into every other supported locale; a failed locale keeps its prior value.

        Failures are collected rather than raised because translation only enriches user-facing text —
        callers such as knowledge-base creation must not fail because one language could not be produced.
        """
        source_text = locale_string.in_locale(source_locale, fallback=False)
        if not source_text:
            logger.warning(f"No source text found for locale {source_locale}")
            return TranslationOutcome(translated=locale_string)

        api_key = await LiteLLMService.api_key_for_user(user)
        llm, _ = llm_config.to_llama_index(api_key=api_key)
        target_locales = [locale for locale in t.supported_locales if locale != source_locale]
        results = await asyncio.gather(
            *(cls._translate_into_locale(source_text, source_locale, locale, llm, t) for locale in target_locales),
            return_exceptions=True,
        )
        return cls._merge_results(locale_string, target_locales, results)

    @staticmethod
    def _merge_results(
        locale_string: LocaleString, target_locales: list[str], results: list[str | BaseException]
    ) -> TranslationOutcome:
        translations: dict[str, str] = {}
        failed_locales: list[str] = []
        for locale, result in zip(target_locales, results, strict=True):
            if isinstance(result, BaseException) and not isinstance(result, Exception):
                raise result
            if isinstance(result, Exception):
                logger.warning(f"Translation into {locale} failed; keeping prior value: {result!r}")
                failed_locales.append(locale)
            else:
                translations[locale] = result
        return TranslationOutcome(
            translated=locale_string.model_copy(update=translations), failed_locales=failed_locales
        )

    @classmethod
    @trace_fn
    async def _translate_into_locale(
        cls, text: str, source_locale: str, target_locale: str, llm: LLM, t: LocaleHandler
    ) -> str:
        """Traced per locale so a failed language shows up as an errored span in Langfuse."""
        response = await llm.apredict(
            PromptTemplate(t("api.common.translation.prompt")),
            source_language=t(f"api.common.translation.{source_locale}"),
            target_language=t(f"api.common.translation.{target_locale}"),
            text=text,
        )
        return cls._extract_translation(response)

    @classmethod
    def _extract_translation(cls, response: str) -> str:
        """Takes the outermost marker pair, so a translated text that itself mentions the tag stays intact.

        The markers are the only signal that the model produced a translation rather than echoing the
        instruction back as prose, which the default model occasionally does.
        """
        match = cls.TRANSLATION_PATTERN.search(response)
        if match is None or not match.group(1).strip():
            raise ValueError(f"Translation model returned no <translation> block: {response[:200]!r}")
        return match.group(1).strip()
