"""LLM classification of one message against a configured category taxonomy."""

import logging

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel, Field, create_model
from swiss_ai_hub.core.imap import EmailClassificationSettings, MailCategory

from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage

logger = logging.getLogger(__name__)

_PROMPT = """{{ instructions }}

Categories:
{% for category in categories %}
{{ loop.index0 }}. {{ category.category }} — {{ category.description }}
{% endfor %}

Message:
From: {{ sender }}
Subject: {{ subject }}

{{ body }}
"""


class CategoryVerdict(BaseModel):
    """Where one message belongs, resolved against the configured taxonomy."""

    category: MailCategory | None
    confidence: float
    reason: str

    @property
    def category_name(self) -> str | None:
        return self.category.category if self.category else None


class MailClassifier:
    """Chooses a category for a message, or declines to.

    The model returns an *index* into the configured list rather than a folder name, so a hostile or confused model
    cannot invent a destination — inbound mail is attacker-controlled and enters this prompt. The worst it can do is
    misfile into a folder the admin already configured.
    """

    @staticmethod
    async def classify(
        parsed: ParsedMessage,
        settings: EmailClassificationSettings,
        llm: LLM,
    ) -> CategoryVerdict:
        selection_model = MailClassifier._selection_model(len(settings.categories))
        selection = await llm.astructured_predict(
            selection_model,
            RichPromptTemplate(_PROMPT),
            instructions=settings.classification_prompt,
            categories=settings.categories,
            sender=parsed.sender,
            subject=parsed.subject,
            body=parsed.body_text or "",
        )
        return MailClassifier._resolve(selection, settings)

    @staticmethod
    def _selection_model(category_count: int) -> type[BaseModel]:
        """Build the response schema from the configured categories so the index cannot address a missing one."""
        return create_model(
            "CategorySelection",
            selected_index=(
                int | None,
                Field(
                    ge=0,
                    lt=category_count,
                    description="Zero-based index of the category that fits, or null when none clearly fits.",
                ),
            ),
            confidence=(
                float,
                Field(ge=0.0, le=1.0, description="How confident you are in this category, from 0.0 to 1.0."),
            ),
            reason=(str, Field(description="One sentence explaining the choice.")),
            __doc__="The category a message belongs to.",
        )

    @staticmethod
    def _resolve(selection: BaseModel, settings: EmailClassificationSettings) -> CategoryVerdict:
        """Two independent routes to 'no category': the model declining, and low confidence.

        Both exist because self-reported confidence is only roughly calibrated — a model that is wrong is often also
        confident, so an explicit "none of these" escape hatch is worth more than the threshold alone.
        """
        index: int | None = selection.selected_index
        confidence: float = selection.confidence
        reason: str = selection.reason

        if index is None:
            return CategoryVerdict(category=None, confidence=confidence, reason=reason)
        if confidence < settings.confidence_threshold:
            logger.info(
                "[classify] confidence %.2f below threshold %.2f — falling back",
                confidence,
                settings.confidence_threshold,
            )
            return CategoryVerdict(category=None, confidence=confidence, reason=reason)
        return CategoryVerdict(category=settings.categories[index], confidence=confidence, reason=reason)
