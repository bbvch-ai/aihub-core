from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.guards.few_shot_guard import few_shot_guard
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.guard import FewShotAcceptEvent, FewShotRejectEvent


async def execute_few_shot_guard(
    condensed_question: str,
    few_shot_examples: list[FewShotGuardExample],
    llm_config: LLMConfig,
    t: LocaleHandler,
    displayer: EventDisplayer,
) -> FewShotRejectEvent | FewShotAcceptEvent:
    """
    Guards the question to ensure it is appropriate for the agent to answer.
    """
    if not few_shot_examples:
        return FewShotAcceptEvent(reason=t("agent.thought.no_few_shot_examples"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        guard_result = await few_shot_guard(
            llm=llm,
            t=t,
            user_query=condensed_question,
            examples=few_shot_examples,
        )

    if not guard_result.success:
        return FewShotRejectEvent(reason=guard_result.reasoning)

    return FewShotAcceptEvent(reason=guard_result.reasoning)
