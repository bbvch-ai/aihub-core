from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.guard import ContextInsufficientRejectEvent, ContextSufficientAcceptEvent

from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.events import ContextInsufficientWithQueryEvent


async def execute_context_sufficient_guard(
    context_content: str,
    user_query: str,
    max_hops: int,
    llm_config: LLMConfig,
    t: LocaleHandler,
    displayer: EventDisplayer,
    run_context: RunContext,
) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
    """
    Guards the context to ensure it is sufficient for generating a response.
    Supports multi-hop retrieval if context is insufficient.

    Note: This step is only called when check_context_sufficiency is enabled.
    The precondition skips this step entirely when disabled.
    """
    prev_queries = await run_context.get("prev_queries", [])
    hop_count = await run_context.get("hop_count", 1)
    more_hops_available = hop_count < max_hops

    async with llm_config.cost_reporting_llm(displayer) as llm:
        guard_result = await context_sufficient_guard(
            llm=llm,
            t=t,
            user_query=user_query,
            context=context_content,
            prev_queries=prev_queries,
            more_hops_available=more_hops_available,
        )

    if guard_result.success:
        await displayer.display_thought(t("agent.thought.context_sufficient"))
        return ContextSufficientAcceptEvent(reason=guard_result.reasoning)

    if not more_hops_available:
        return ContextInsufficientRejectEvent(reason=guard_result.reasoning)

    await run_context.set("hop_count", hop_count + 1)
    new_query = guard_result.new_query
    prev_queries.append(new_query)
    await run_context.set("prev_queries", prev_queries)
    await displayer.display_thought(t("agent.thought.trying_another_retrieval_hop"))
    return ContextInsufficientWithQueryEvent(reason=guard_result.reasoning, new_query=new_query)
