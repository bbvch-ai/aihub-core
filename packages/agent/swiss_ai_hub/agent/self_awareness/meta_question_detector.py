import logging

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from openai import APIError, BadRequestError
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.self_awareness.meta_question_classification import MetaQuestionClassification

logger = logging.getLogger(__name__)

_LABEL_TO_CATEGORY = {
    "META_IDENTITY": "identity",
    "META_CAPABILITIES": "capabilities",
    "META_BEHAVIOR": "behavior",
}
_LABELS = (*_LABEL_TO_CATEGORY, "NORMAL")

# Detection and the meta answer are trivial for a reasoning model, so its thinking is pure latency (≈13s
# for a single-token classification on Qwen3.5). Model families read different keys — Qwen3 honours
# ``enable_thinking`` and silently ignores ``thinking``, other vLLM templates honour ``thinking`` — so send
# both. Mistral-tokenizer models (Ministral) reject ``chat_template_kwargs`` with a 400; callers fall back
# to a plain request.
REASONING_DISABLED_EXTRA_BODY = {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}

# Reasoning models on Infomaniak cannot reliably produce structured output (tool calls / JSON) but are
# reliable at emitting a single free-text label, so detection classifies via a plain-text token. Tokens
# are language-agnostic; the model reads the (any-language) user message and emits the English token.
#
# Prompt shape decides whether a weak instruction-follower can use this at all. An earlier revision listed
# NORMAL first with the longest elaboration and closed with "When in doubt, answer NORMAL." — on Apertus-70B
# that collapsed to NORMAL for *every* meta question, including the prompt's own verbatim examples, so the
# self-awareness branch became unreachable. Hence three properties worth preserving: META_ labels lead,
# the "do you know X?" lookalike carve-outs live inside NORMAL's own definition rather than as a closing
# tie-breaker, and each label carries non-English anchors (without them "Was kannst du?" reads as NORMAL).
_CLASSIFICATION_PROMPT = """You classify a user's message to an AI assistant. Decide what the message is \
*about*: the assistant itself, or the world.

The message may be in any language; always reply with the English token.

Reply with EXACTLY ONE token on the final line, and nothing else:
- META_IDENTITY — who or what the assistant is. "who are you?", "what is your name?", "are you a human?", \
"Wer bist du?", "Qui es-tu ?", "Chi sei?"
- META_CAPABILITIES — what the assistant can or cannot do, or what to use it for. "what can you do?", \
"can you help me?", "what are your limits?", "Was kannst du?", "Que peux-tu faire ?", "Cosa sai fare?"
- META_BEHAVIOR — why the assistant did something, or how it works internally. "why did you answer that \
way?", "how do you work?", "where did you get that from?", "Wie funktionierst du?", "Comment fonctionnes-tu ?"
- NORMAL — everything else: a task to perform, or a question about a topic, place, person, organization, \
document, or field of knowledge — even when phrased "do you know X?", "what do you know about X?", or \
"what can I do with this document?".

Decide by the subject of the message: if the subject is the assistant, pick the matching META_ label; if it \
is anything else, pick NORMAL.

User message: "{user_query}"
Answer:"""


def _parse_label(text: str) -> str | None:
    """Pick the last token mentioned, so a label in the final answer wins over any in the reasoning."""
    upper = text.upper()
    matches = [(upper.rfind(label), label) for label in _LABELS if label in upper]
    return max(matches)[1] if matches else None


async def detect_meta_question(llm: LLM, t: LocaleHandler, user_query: str) -> MetaQuestionClassification:
    """Classify whether a user message is a meta question about the agent itself.

    Detection gates every chat message, so it must never fail the run: if the model returns no
    recognizable label, fall back to "not a meta question" and let the normal answer pipeline handle it.
    """
    prompt = PromptTemplate(_CLASSIFICATION_PROMPT)
    message = ChatMessage(role=MessageRole.USER, content=prompt.format(user_query=user_query))

    try:
        # Disable reasoning: this is a trivial single-token classification, so the model's thinking is
        # pure latency. Mistral-tokenizer models reject chat_template_kwargs, so fall back to a plain call
        # (they have no reasoning to disable anyway).
        try:
            response = await llm.achat([message], extra_body=REASONING_DISABLED_EXTRA_BODY)
        except BadRequestError:
            response = await llm.achat([message])
        raw_answer = str(response.message.content)
        label = _parse_label(raw_answer)
        degraded_reason = None if label is not None else f"unrecognized classification {raw_answer.strip()[:80]!r}"
    except (APIError, ValueError, TypeError) as detection_failure:
        # Detection gates every chat message, so a transient gateway error (timeout, connection,
        # rate-limit, 5xx — all openai.APIError) or an unparseable response must degrade to the normal
        # pipeline, never surface as an ExceptionEvent that kills an otherwise-healthy run.
        logger.warning(
            "Meta-question detection failed (%s); treating as a normal question.", type(detection_failure).__name__
        )
        label = None
        degraded_reason = f"detection call failed ({type(detection_failure).__name__})"

    category = _LABEL_TO_CATEGORY.get(label or "")
    if category is not None:
        return MetaQuestionClassification(
            is_meta_question=True,
            category=category,
            reasoning="Classified as a meta question about the assistant.",
        )
    # Spell out *why* the normal pipeline was chosen: a genuine NORMAL verdict and a degraded fallback used to
    # emit the same reasoning, which made a silently-failing classifier indistinguishable from a working one
    # in the persisted event log.
    if degraded_reason is not None:
        return MetaQuestionClassification(
            is_meta_question=False,
            reasoning=f"Defaulted to a normal task for the assistant: {degraded_reason}.",
        )
    return MetaQuestionClassification(
        is_meta_question=False,
        reasoning="Classified as a normal task for the assistant.",
    )
