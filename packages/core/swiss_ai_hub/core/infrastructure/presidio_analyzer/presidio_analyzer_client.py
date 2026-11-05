from typing import Annotated

import httpx

from swiss_ai_hub.core.infrastructure.presidio_analyzer.analyzer_span import AnalyzerSpan
from swiss_ai_hub.core.infrastructure.presidio_analyzer.presidio_analyzer_settings import PresidioAnalyzerSettings


class PresidioAnalyzerClient:
    """The deployment's Presidio analyzer: finds personal data in a text without the text leaving the deployment.

    Every text is analysed as `de`, the one language the analyzer registers its recognizers under; its GLiNER model
    covers French, Italian and English text sent that way. A failed analysis raises, so a caller never treats an
    unanalysed text as clean.
    """

    LANGUAGE = "de"

    def __init__(self, settings: PresidioAnalyzerSettings | None = None) -> None:
        self._settings = settings or PresidioAnalyzerSettings()

    async def analyze(
        self,
        text: Annotated[str, "The text to search for personal data."],
        entities: Annotated[list[str], "The entity types to report."],
        allow_list_pattern: Annotated[str | None, "Spans matching this regex in full are not reported."] = None,
    ) -> list[AnalyzerSpan]:
        body: dict = {"text": text, "language": self.LANGUAGE, "entities": entities}
        if allow_list_pattern:
            body |= {"allow_list": [allow_list_pattern], "allow_list_match": "regex"}
        headers = {"Authorization": f"Bearer {self._settings.API_KEY.get_secret_value()}"}
        async with httpx.AsyncClient(timeout=self._settings.TIMEOUT) as client:
            response = await client.post(f"{self._settings.API_BASE.rstrip('/')}/analyze", json=body, headers=headers)
        response.raise_for_status()
        return [AnalyzerSpan.model_validate(span) for span in response.json()]
