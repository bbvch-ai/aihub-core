import logging

from llama_index.core import PromptTemplate
from pydantic import ValidationError
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import LiteLLMProxySettings, trace_fn

from swiss_ai_hub.api.routes.translation.dto.translation_request import TranslationRequest
from swiss_ai_hub.api.routes.translation.dto.translation_response import TranslationResponse

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for automatically translating content to all supported locales using a single LLM call.
    """

    DEFAULT_MODEL = "text-generation/gemma-4-31B-it"

    @classmethod
    @trace_fn
    async def translate_from_request(cls, request: TranslationRequest, t: LocaleHandler) -> TranslationResponse:
        """
        Translates a LocaleString from the request to all supported locales.
        """
        model_name = request.model_name or cls._get_default_model()
        llm_config = LLMConfig(model_name=model_name)

        translated = await cls.translate(
            locale_string=request.text,
            llm_config=llm_config,
            t=t,
            source_locale=request.source_locale,
        )

        return TranslationResponse(translated=translated)

    @classmethod
    def _get_default_model(cls) -> str:
        """Get a default model for translation from LiteLLM settings or fallback."""
        try:
            settings = LiteLLMProxySettings()
            if settings.DEFAULT_MODEL:
                return settings.DEFAULT_MODEL
        except Exception:
            pass
        return cls.DEFAULT_MODEL

    @classmethod
    @trace_fn
    async def translate(
        cls, locale_string: LocaleString, llm_config: LLMConfig, t: LocaleHandler, source_locale: str = "en"
    ) -> LocaleString:
        """
        Translates fields in a translatable object (LocaleString).
        """
        source_text = locale_string.in_locale(source_locale, fallback=False)
        if not source_text:
            logger.warning(f"No source text found for locale {source_locale}")
            return locale_string

        target_locales = [locale for locale in t.supported_locales if locale != source_locale]
        new_translations = await cls._get_translations_from_llm(
            text=source_text,
            source_language_code=source_locale,
            target_language_codes=target_locales,
            llm_config=llm_config,
            t=t,
        )
        if new_translations is None:
            return locale_string
        final_data = locale_string.model_dump()
        new_data = new_translations.model_dump(exclude_unset=True)
        final_data.update(new_data)
        return LocaleString(**final_data)

    @classmethod
    async def _get_translations_from_llm(
        cls,
        text: str,
        source_language_code: str,
        target_language_codes: list[str],
        llm_config: LLMConfig,
        t: LocaleHandler,
    ) -> LocaleString | None:
        """Returns the parsed translations, or ``None`` when the model produced no valid JSON.

        The translation model (a small instruct model) is not reliable at emitting JSON — it
        occasionally echoes the instruction back as prose. Since translation only enriches
        user-facing text with extra locales, a non-parseable response must degrade to "no
        translation" rather than fail the caller's core operation.
        """
        llm, _ = llm_config.to_llama_index()
        target_languages = ", ".join([t(f"api.common.translation.{lang}") for lang in target_language_codes])
        prompt = PromptTemplate(t("api.common.translation.prompt"))
        response = await llm.apredict(
            prompt,
            source_language=t(f"api.common.translation.{source_language_code}"),
            target_languages=target_languages,
            locale_codes=target_language_codes,
            text=text,
        )
        return cls._parse_locale_string(response)

    @staticmethod
    def _parse_locale_string(response: str) -> LocaleString | None:
        """Extracts a ``LocaleString`` from a raw model response, tolerating fences and stray prose."""
        candidate = response.strip()
        if candidate.startswith("```"):
            candidate = candidate.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        start, end = candidate.find("{"), candidate.rfind("}")
        if start == -1 or end <= start:
            logger.warning(f"Translation model returned no JSON object; skipping translation. Response: {response!r}")
            return None

        try:
            return LocaleString.model_validate_json(candidate[start : end + 1])
        except ValidationError:
            logger.warning(f"Translation model returned unparseable JSON; skipping translation. Response: {response!r}")
            return None
