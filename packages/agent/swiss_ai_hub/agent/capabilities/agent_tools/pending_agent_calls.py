from swiss_ai_hub.agent.capabilities.agent_tools.pending_agent_call import PendingAgentCall
from swiss_ai_hub.agent.context.run.run_context import RunContext


class PendingAgentCalls:
    """The delegations a run's tool calls are waiting on, by the request's event id the answer names."""

    _KEY = "agent_tools:pending:{request_event_id}"

    @staticmethod
    async def keep(request_event_id: str, call: PendingAgentCall, run_context: RunContext) -> None:
        await run_context.set(PendingAgentCalls._KEY.format(request_event_id=request_event_id), call.model_dump())

    @staticmethod
    async def find(request_event_id: str, run_context: RunContext) -> PendingAgentCall | None:
        call = await run_context.get(PendingAgentCalls._KEY.format(request_event_id=request_event_id))
        return PendingAgentCall.model_validate(call) if call else None
