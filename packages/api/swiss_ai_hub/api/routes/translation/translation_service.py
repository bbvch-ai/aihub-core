import asyncio
import logging

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import LiteLLMService, trace_fn

from swiss_ai_hub.api.routes.translation.dto.translation_outcome import TranslationOutcome
from swiss_ai_hub.api.routes.translation.dto.translation_request import TranslationRequest
from swiss_ai_hub.api.routes.translation.dto.translation_response import TranslationResponse
from swiss_ai_hub.api.routes.translation.missing_translation_error import MissingTranslationError

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for translating content into all supported locales, one concurrent LLM call per target locale.

    One call per locale keeps a single bad generation from discarding the others, and avoids wrapping
    large texts (agent system prompts) in a JSON envelope the model has to escape correctly.
    """

    DEFAULT_MODEL = "text-generation/gemma-4-31B-it"
    OPENING_MARKER = "<translation>"
    CLOSING_MARKER = "</translation>"

    @classmethod
    @trace_fn
    async def translate_from_request(
        cls, request: TranslationRequest, t: LocaleHandler, user: UserIdentity
    ) -> TranslationResponse:
        """
        Fills in the empty locales of the LocaleString from the request.
        """
        llm_config = LLMConfig.deterministic(request.model_name or cls.DEFAULT_MODEL)
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
        Fills in every supported locale that has no value yet by translating the source locale.

        Locales that already have a value are left alone, so a retry after a partial failure fills in only the
        missing ones and never overwrites translations the user has corrected. A generation without a usable
        <translation> block counts as a failed locale; gateway and configuration errors propagate.
        """
        source_text = locale_string.in_locale(source_locale, fallback=False)
        if not source_text:
            logger.warning(f"No source text found for locale {source_locale}")
            return TranslationOutcome(translated=locale_string)

        target_locales = [
            locale
            for locale in t.supported_locales
            if locale != source_locale and not locale_string.in_locale(locale, fallback=False)
        ]
        if not target_locales:
            return TranslationOutcome(translated=locale_string)

        api_key = await LiteLLMService.api_key_for_user(user)
        llm, _ = llm_config.to_llama_index(api_key=api_key)
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
            if isinstance(result, MissingTranslationError):
                logger.warning(f"Translation into {locale} failed; leaving it empty: {result}")
                failed_locales.append(locale)
            elif isinstance(result, BaseException):
                raise result
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
        return cls._extract_translation(response, text)

    @classmethod
    def _extract_translation(cls, response: str, source_text: str) -> str:
        """Closes the block at the closing marker matching the ones the source text itself contains.

        Neither the first nor the last closing marker is right: the first cuts a text that mentions the tag, the
        last sweeps a repeated block or a trailing note into the saved text. The markers are the only signal that
        the model produced a translation rather than echoing the instruction back as prose.
        """
        start = response.find(cls.OPENING_MARKER)
        if start == -1:
            raise MissingTranslationError(f"Translation model returned no <translation> block: {response[:200]!r}")
        segments = response[start + len(cls.OPENING_MARKER) :].split(cls.CLOSING_MARKER)
        segments_in_translation = source_text.count(cls.CLOSING_MARKER) + 1
        if len(segments) <= segments_in_translation:
            raise MissingTranslationError(
                f"Translation model returned an unclosed <translation> block: {response[:200]!r}"
            )
        translation = cls.CLOSING_MARKER.join(segments[:segments_in_translation]).strip()
        if not translation:
            raise MissingTranslationError(
                f"Translation model returned an empty <translation> block: {response[:200]!r}"
            )
        return translation
