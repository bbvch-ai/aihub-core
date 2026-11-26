from swiss_ai_hub.core.events.agent import ToolApprovalRequestEvent

from swiss_ai_hub.agent.context.run.run_context import RunContext


class PendingToolApprovals:
    """The approval requests a run is waiting on, kept in the run's context by request id.

    The answer a chat client sends back carries its own copy of the request, which the client is free to change.
    Only the stored request decides what runs, and taking it removes it, so one request is answered at most once.
    """

    @staticmethod
    async def keep(request: ToolApprovalRequestEvent, run_context: RunContext) -> None:
        await run_context.set(PendingToolApprovals._key(request.event_id), request.model_dump(mode="json"))

    @staticmethod
    async def take(request_id: str, run_context: RunContext) -> ToolApprovalRequestEvent | None:
        stored = await run_context.pop(PendingToolApprovals._key(request_id))
        return ToolApprovalRequestEvent.model_validate(stored) if stored else None

    @staticmethod
    def _key(request_id: str) -> str:
        return f"tool_loop:pending_approval:{request_id}"
