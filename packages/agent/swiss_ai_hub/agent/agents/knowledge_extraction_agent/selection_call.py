from pydantic import ValidationError
from swiss_ai_hub.core.events.agent import ToolCallApprovedEvent, ToolCallsDecidedEvent, ToolResultEvent

from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import SELECT_KNOWLEDGE_DOCUMENTS_TOOL


class SelectionCall:
    """The selection the discovery loop settled on: its last successful `select_knowledge_documents` call.

    Calls are ordered by the loop's own record of when the model made them, iteration then position, because their
    events are created by parallel tasks and their timestamps do not say which came last.
    """

    @staticmethod
    def last(
        decided: list[ToolCallsDecidedEvent] | None,
        calls: list[ToolCallApprovedEvent] | None,
        results: list[ToolResultEvent] | None,
    ) -> ExtractRecordsArguments | None:
        order = SelectionCall._order(decided)
        succeeded = SelectionCall._succeeded(results, {SELECT_KNOWLEDGE_DOCUMENTS_TOOL})
        selections = sorted(
            (
                call
                for call in calls or []
                if call.name == SELECT_KNOWLEDGE_DOCUMENTS_TOOL and call.tool_call_id in succeeded
            ),
            key=lambda call: order.get(call.tool_call_id, (-1, -1)),
            reverse=True,
        )
        for call in selections:
            try:
                return ExtractRecordsArguments.model_validate(call.arguments)
            except ValidationError:
                continue
        return None

    @staticmethod
    def _order(decided: list[ToolCallsDecidedEvent] | None) -> dict[str, tuple[int, int]]:
        return {
            call_id: (event.state.iteration, position)
            for event in decided or []
            for position, call_id in enumerate(event.tool_call_ids)
        }

    @staticmethod
    def _succeeded(results: list[ToolResultEvent] | None, names: set[str]) -> set[str]:
        return {result.tool_call_id for result in results or [] if result.name in names and not result.is_error}
