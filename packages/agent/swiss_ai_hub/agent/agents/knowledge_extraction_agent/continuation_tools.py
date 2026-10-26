from typing import Annotated

from llama_index.core.tools.tool_spec.base import BaseToolSpec

from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

CONTINUE_EXTRACTION_TOOL = "continue_extraction"


class ContinuationTools(BaseToolSpec):
    """Lets the model go on with the table extraction an earlier answer left unfinished, once the user agrees.

    The call only states the decision: the blueprint reads it after the loop and extracts the next part. It is offered
    only while an extraction is pending, so the model cannot continue something that does not exist.
    """

    spec_functions = [CONTINUE_EXTRACTION_TOOL]

    def __init__(self, context: ToolContext) -> None:
        self.context = context

    @ToolOptions.of(label=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.tools.continue.label"))
    async def continue_extraction(
        self, user_agreed: Annotated[bool, "True when the user asked to go on with the unfinished extraction"] = True
    ) -> str:
        """Goes on with the table extraction an earlier answer left unfinished: its next rows or documents, with the
        same columns. Call it only when the user agrees to continue, then stop."""
        if not user_agreed:
            return "Nothing continues. Answer the user's new request instead."
        return "The next part of the unfinished extraction runs after this turn. Reply with one short sentence."
