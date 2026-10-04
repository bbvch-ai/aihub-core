import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from openai import APIError
from swiss_ai_hub.core.generative_ai import ReasoningFreeChat
from swiss_ai_hub.core.imap import MAX_SUBJECT_CHARACTERS, ParsedMessage

logger = logging.getLogger(__name__)

_LABEL_TO_LOCALE = {"DE": "de", "EN": "en", "FR": "fr", "IT": "it"}
_LABELS = (*_LABEL_TO_LOCALE, "OTHER")

# Name and salutation per locale. The salutation example is not decoration: without it a drafting prompt that
# prescribes „Guten Tag Frau/Herr [Nachname]" kept that greeting on top of an otherwise English reply.
_REPLY_LANGUAGES = {
    "de": ("German", "Guten Tag Herr Muster"),
    "en": ("English", "Dear Mr Smith"),
    "fr": ("French", "Bonjour Monsieur Dupont"),
    "it": ("Italian", "Buongiorno Signor Rossi"),
}

# The opening of a message is what says which language it is written in; a quoted thread further down is often in
# another one, and the rest only costs tokens.
_MAX_BODY_CHARACTERS = 1500

# A single free-text label rather than structured output: reasoning models on this gateway are reliable at the one
# and not the other (see `meta_question_detector`).
_DETECTION_PROMPT = """Which language is the following email written in? Judge the sender's own text, not quoted \
earlier messages or signatures.

Reply with EXACTLY ONE token on the final line, and nothing else: DE (German), EN (English), FR (French), IT \
(Italian), or OTHER.

Subject: {subject}

{body}

Answer:"""


class MailLanguageDetector:
    """Decides which language a delegated run drafts a reply in.

    A scheduled run has no user and runs in the platform default locale, and the drafting prompt an admin writes is
    usually in one language with fixed phrases in it. The one line of such a prompt asking for the sender's language
    lost to both often enough that English mail regularly got German drafts (aihub-core-private#299), and switching
    the delegated locale alone changed nothing, so the detected language is also stated to the model up front.
    """

    @staticmethod
    async def detect(llm: LLM, parsed: ParsedMessage) -> str | None:
        """The locale `parsed` is written in, or None when the model cannot say. Never raises.

        Detection only picks the language a draft is framed in, so it must not cost the message its draft: an
        unrecognised answer, a language the platform has no locale for, or a gateway failure is reported as None and
        the caller keeps the behaviour from before detection existed.
        """
        prompt = _DETECTION_PROMPT.format(
            subject=parsed.subject[:MAX_SUBJECT_CHARACTERS],
            body=(parsed.body_text or "").strip()[:_MAX_BODY_CHARACTERS],
        )
        message = ChatMessage(role=MessageRole.USER, content=prompt)
        try:
            response = await ReasoningFreeChat.achat(llm, [message])
        except (APIError, ValueError, TypeError) as detection_failure:
            logger.warning(
                "[draft] language detection for uid=%s failed (%s) — drafting without a language directive",
                parsed.message_id,
                type(detection_failure).__name__,
            )
            return None

        label = MailLanguageDetector.parse_label(str(response.message.content))
        return _LABEL_TO_LOCALE.get(label or "")

    @staticmethod
    def parse_label(text: str) -> str | None:
        """The last label the answer mentions, so the final answer wins over any label in the model's reasoning."""
        tokens = [token.strip(".,:;!?\"'`*()[]") for token in text.upper().split()]
        labels = [token for token in tokens if token in _LABELS]
        return labels[-1] if labels else None

    @staticmethod
    def with_reply_language(draft_prompt: str, locale: str) -> str:
        """`draft_prompt` led by a directive to write the whole reply in the language of `locale`.

        Leading, and in the system prompt: appended at the end of a long prompt it did not reach the salutation, and
        placed in the user message it leaked into the RAG agent's condensed search query and degraded retrieval.
        """
        language, salutation = _REPLY_LANGUAGES[locale]
        directive = (
            f"REPLY LANGUAGE: {language}. The incoming email is written in {language}, so write the entire draft in "
            f'{language} — including the salutation (for example "{salutation}"), the closing sentence and the '
            f"sign-off. Wherever the instructions below prescribe a fixed phrase in another language, use its "
            f"{language} equivalent instead."
        )
        return f"{directive}\n\n{draft_prompt}"
