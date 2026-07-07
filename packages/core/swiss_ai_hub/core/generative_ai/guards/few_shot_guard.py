import logging

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM

from swiss_ai_hub.core.generative_ai.guards.guard_result import GuardResult
from swiss_ai_hub.core.generative_ai.guards.text_verdict import (
    binary_verdict_instruction,
    parse_binary_verdict,
    request_verdict,
)
from swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_guard_example import FewShotGuardExample
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

logger = logging.getLogger(__name__)

_ALLOW, _BLOCK = "ALLOW", "BLOCK"


async def few_shot_guard(
    examples: list[FewShotGuardExample],
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
) -> GuardResult:
    user_template = PromptTemplate(t("lib.guards.few_shot_guard.user_message"))
    success_template = PromptTemplate(t("lib.guards.few_shot_guard.success_message"))
    reason_template = PromptTemplate(t("lib.guards.few_shot_guard.reason_message"))

    def format_example(example: FewShotGuardExample) -> str:
        return "".join(
            [
                user_template.format(user=example.user.in_locale(t.locale)),
                success_template.format(success=example.success),
                reason_template.format(reason=example.reason.in_locale(t.locale)),
            ]
        )

    joined_examples = "".join(format_example(example) for example in examples)
    prompt = PromptTemplate(t("lib.guards.few_shot_guard.prompt")).format(
        examples=joined_examples,
        user_query=user_query,
    ) + binary_verdict_instruction(_ALLOW, _BLOCK)

    verdict = parse_binary_verdict(await request_verdict(llm, prompt), _ALLOW, _BLOCK)
    if verdict is None:
        # Reasoning models occasionally return no recognizable verdict; accept rather than block the user.
        logger.warning("Few-shot guard returned no verdict; accepting the request.")
        return GuardResult(success=True, reasoning="Guard unavailable; accepting the request.")
    return GuardResult(success=verdict.success, reasoning=verdict.reasoning)
