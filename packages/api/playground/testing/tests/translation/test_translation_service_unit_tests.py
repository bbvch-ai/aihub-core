from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.routes.translation.translation_service import TranslationService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.translation.translation_service"


class TestParseLocaleString:
    def test_parses_bare_json(self):
        result = TranslationService._parse_locale_string('{"en": "hi", "de": "hallo"}')
        assert result is not None
        assert result.model_dump(exclude_unset=True) == {"en": "hi", "de": "hallo"}

    def test_parses_json_wrapped_in_markdown_fence(self):
        result = TranslationService._parse_locale_string('```json\n{"de": "hallo"}\n```')
        assert result is not None
        assert result.model_dump(exclude_unset=True) == {"de": "hallo"}

    def test_extracts_json_object_surrounded_by_prose(self):
        result = TranslationService._parse_locale_string('Sure! Here it is: {"fr": "bonjour"} — done.')
        assert result is not None
        assert result.model_dump(exclude_unset=True) == {"fr": "bonjour"}

    def test_returns_none_when_response_is_prose_without_json(self):
        result = TranslationService._parse_locale_string("Bitte geben Sie den zu übersetzenden Text an.")
        assert result is None

    def test_returns_none_when_json_is_malformed(self):
        result = TranslationService._parse_locale_string('{"de": ')
        assert result is None


class TestTranslateFallsBackWhenModelReturnsNoJson:
    @pytest.mark.asyncio
    async def test_returns_source_locale_string_untranslated_on_unparseable_response(self):
        source = LocaleString(en="My Namespace")
        t = MagicMock(side_effect=lambda key: key)
        t.locale = "en"
        t.supported_locales = ["en", "de", "fr", "it"]

        llm = MagicMock()
        llm.apredict = AsyncMock(return_value="Bitte geben Sie den zu übersetzenden Text an.")
        llm_config = MagicMock()
        llm_config.to_llama_index.return_value = (llm, None)

        with patch(f"{_SERVICE_MODULE}.PromptTemplate"):
            result = await TranslationService.translate(
                locale_string=source, llm_config=llm_config, t=t, source_locale="en"
            )

        assert result.model_dump(exclude_unset=True) == {"en": "My Namespace"}
