import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.routes.translation.dto.translation_request import TranslationRequest
from swiss_ai_hub.api.routes.translation.missing_translation_error import MissingTranslationError
from swiss_ai_hub.api.routes.translation.translation_service import TranslationService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.translation.translation_service"


class TestExtractTranslation:
    def test_extracts_text_between_markers(self):
        assert TranslationService._extract_translation("<translation>Hallo</translation>", "Hello") == "Hallo"

    def test_ignores_preamble_and_trailing_prose(self):
        response = "Voici la traduction :\n<translation>\nBonjour\n</translation>\nJ'espère que cela aide."
        assert TranslationService._extract_translation(response, "Hello") == "Bonjour"

    def test_extracts_from_inside_markdown_fence(self):
        response = "```\n<translation>Ciao</translation>\n```"
        assert TranslationService._extract_translation(response, "Hello") == "Ciao"

    def test_keeps_inner_tags_and_backslashes_verbatim(self):
        translated = '<persona>\nDu bist ein Assistent.\n</persona>\n<tone>\n- Antworte "präzise" \\ knapp.\n</tone>'
        assert TranslationService._extract_translation(f"<translation>{translated}</translation>", "...") == translated

    def test_keeps_the_tag_when_the_source_text_mentions_it(self):
        source = "Use <translation> and </translation> as markers."
        response = "<translation>Verwende <translation> und </translation> als Marker.</translation>"
        assert TranslationService._extract_translation(response, source) == (
            "Verwende <translation> und </translation> als Marker."
        )

    def test_takes_only_the_first_block_when_the_model_repeats_it(self):
        response = "<translation>Hallo</translation>\n<translation>Hallo</translation>"
        assert TranslationService._extract_translation(response, "Hello") == "Hallo"

    def test_drops_a_trailing_note_that_mentions_the_tag(self):
        response = "<translation>Hallo</translation>\nNote: everything up to </translation> is the translation."
        assert TranslationService._extract_translation(response, "Hello") == "Hallo"

    def test_raises_when_markers_are_missing(self):
        with pytest.raises(MissingTranslationError, match="no <translation> block"):
            TranslationService._extract_translation("Bitte geben Sie den zu übersetzenden Text an.", "Hello")

    def test_raises_when_the_block_is_not_closed(self):
        with pytest.raises(MissingTranslationError, match="unclosed <translation> block"):
            TranslationService._extract_translation("<translation>Hallo, wie geht", "Hello, how are you")

    def test_raises_when_markers_are_empty(self):
        with pytest.raises(MissingTranslationError, match="empty <translation> block"):
            TranslationService._extract_translation("<translation>   </translation>", "Hello")


def _locale_handler() -> MagicMock:
    t = MagicMock(side_effect=lambda key: key)
    t.locale = "en"
    t.supported_locales = ["en", "de", "fr", "it"]
    return t


def _llm_config_returning(apredict: AsyncMock) -> MagicMock:
    llm = MagicMock()
    llm.apredict = apredict
    llm_config = MagicMock()
    llm_config.to_llama_index.return_value = (llm, None)
    return llm_config


def _per_locale_responses(responses: dict[str, str | Exception]) -> AsyncMock:
    async def respond(_prompt, **kwargs):
        response = responses[kwargs["target_language"].rsplit(".", 1)[-1]]
        if isinstance(response, Exception):
            raise response
        return response

    return AsyncMock(side_effect=respond)


async def _translate(source: LocaleString, apredict: AsyncMock, source_locale: str = "en"):
    with (
        patch(f"{_SERVICE_MODULE}.PromptTemplate"),
        patch(f"{_SERVICE_MODULE}.LiteLLMService.api_key_for_user", new_callable=AsyncMock),
    ):
        return await TranslationService.translate(
            locale_string=source,
            llm_config=_llm_config_returning(apredict),
            t=_locale_handler(),
            user=MagicMock(),
            source_locale=source_locale,
        )


class TestTranslate:
    @pytest.mark.asyncio
    async def test_translates_every_target_locale_in_its_own_call(self):
        apredict = _per_locale_responses(
            {
                "de": "<translation>Hallo</translation>",
                "fr": "<translation>Bonjour</translation>",
                "it": "<translation>Ciao</translation>",
            }
        )

        outcome = await _translate(LocaleString(en="Hello"), apredict)

        assert apredict.await_count == 3
        assert outcome.translated.model_dump() == {"en": "Hello", "de": "Hallo", "fr": "Bonjour", "it": "Ciao"}
        assert outcome.failed_locales == []

    @pytest.mark.asyncio
    async def test_runs_the_locale_calls_concurrently(self):
        in_flight = 0
        peak = 0

        async def respond(_prompt, **_kwargs):
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return "<translation>x</translation>"

        await _translate(LocaleString(en="Hello"), AsyncMock(side_effect=respond))

        assert peak == 3

    @pytest.mark.asyncio
    async def test_translates_only_the_locales_that_are_still_empty(self):
        apredict = _per_locale_responses({"de": "<translation>Hallo</translation>"})

        outcome = await _translate(LocaleString(en="Hello", fr="Salut (corrigé)", it="Ciao (corretto)"), apredict)

        assert apredict.await_count == 1
        assert outcome.translated.model_dump() == {
            "en": "Hello",
            "de": "Hallo",
            "fr": "Salut (corrigé)",
            "it": "Ciao (corretto)",
        }
        assert outcome.failed_locales == []

    @pytest.mark.asyncio
    async def test_skips_the_llm_when_every_locale_already_has_a_value(self):
        apredict = AsyncMock()

        outcome = await _translate(LocaleString(en="Hello", de="Hallo", fr="Salut", it="Ciao"), apredict)

        apredict.assert_not_awaited()
        assert outcome.failed_locales == []

    @pytest.mark.asyncio
    async def test_a_gateway_error_propagates_instead_of_counting_as_a_failed_locale(self):
        apredict = _per_locale_responses(
            {
                "de": "<translation>Hallo</translation>",
                "fr": RuntimeError("gateway timeout"),
                "it": "<translation>Ciao</translation>",
            }
        )

        with pytest.raises(RuntimeError, match="gateway timeout"):
            await _translate(LocaleString(en="Hello"), apredict)

    @pytest.mark.asyncio
    async def test_a_response_without_markers_counts_as_failed(self):
        apredict = _per_locale_responses(
            {
                "de": "Bitte geben Sie den zu übersetzenden Text an.",
                "fr": "<translation>Bonjour</translation>",
                "it": "<translation>Ciao</translation>",
            }
        )

        outcome = await _translate(LocaleString(en="Hello"), apredict)

        assert outcome.translated.de is None
        assert outcome.failed_locales == ["de"]

    @pytest.mark.asyncio
    async def test_all_locales_failing_returns_the_source_untouched(self):
        apredict = AsyncMock(return_value="I cannot translate this text.")

        outcome = await _translate(LocaleString(en="Hello"), apredict)

        assert outcome.translated.model_dump(exclude_unset=True) == {"en": "Hello"}
        assert outcome.failed_locales == ["de", "fr", "it"]

    @pytest.mark.asyncio
    async def test_cancellation_propagates_instead_of_counting_as_a_failed_locale(self):
        apredict = AsyncMock(side_effect=asyncio.CancelledError())

        with pytest.raises(asyncio.CancelledError):
            await _translate(LocaleString(en="Hello"), apredict)

    @pytest.mark.asyncio
    async def test_missing_source_text_skips_the_llm(self):
        apredict = AsyncMock()

        outcome = await _translate(LocaleString(de="Hallo"), apredict, source_locale="en")

        apredict.assert_not_awaited()
        assert outcome.translated.model_dump(exclude_unset=True) == {"de": "Hallo"}
        assert outcome.failed_locales == []


class TestTranslateFromRequest:
    @pytest.mark.asyncio
    async def test_uses_default_model_and_exposes_failed_locales(self):
        apredict = _per_locale_responses(
            {
                "de": "<translation>Hallo</translation>",
                "fr": "Bitte geben Sie den zu übersetzenden Text an.",
                "it": "<translation>Ciao</translation>",
            }
        )
        llm_config = _llm_config_returning(apredict)

        with (
            patch(f"{_SERVICE_MODULE}.PromptTemplate"),
            patch(f"{_SERVICE_MODULE}.LiteLLMService.api_key_for_user", new_callable=AsyncMock),
            patch(f"{_SERVICE_MODULE}.LLMConfig.deterministic", return_value=llm_config) as deterministic_config,
        ):
            response = await TranslationService.translate_from_request(
                TranslationRequest(text=LocaleString(en="Hello")), _locale_handler(), MagicMock()
            )

        deterministic_config.assert_called_once_with(TranslationService.DEFAULT_MODEL)
        assert response.translated.model_dump() == {"en": "Hello", "de": "Hallo", "fr": None, "it": "Ciao"}
        assert response.failed_locales == ["fr"]
