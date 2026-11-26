from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_set import ToolSet
from swiss_ai_hub.agent.context.run.run_context import RunContext


class ToolAvailability:
    """Whether a tool may run in this run: the blueprint declares it, the profile does not disable it and the chat
    toggle it needs is on.

    Checked again wherever a call is about to run, not only when the model is offered its tools, since an approval
    arrives from outside the run.
    """

    @staticmethod
    async def allows(
        name: str, tool_set: ToolSet | None, config: ToolLoopConfig, run_context: RunContext, blueprint: type[Agent]
    ) -> bool:
        if tool_set is None or tool_set.kind(name) is None or config.is_disabled(name):
            return False
        feature = tool_set.options(name).chat_feature
        return feature is None or await RequestedFeatures.contains(feature, run_context, blueprint)
