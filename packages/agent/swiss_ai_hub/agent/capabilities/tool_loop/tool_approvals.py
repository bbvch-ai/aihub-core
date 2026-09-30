from swiss_ai_hub.agent.capabilities.tool_loop.declared_tool import DeclaredTool
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext


class ToolApprovals:
    """Which calls need the user's approval, and which approvals the user already gave for the run or conversation."""

    @staticmethod
    def policy(tool: DeclaredTool, config: ToolLoopConfig) -> ToolApprovalPolicy:
        """The profile's rule, else the tool's default; a tool approved per call never lets an approval carry over."""
        rule = config.approval_rule_for(tool.name)
        policy = ToolApprovalPolicy(rule.policy) if rule else tool.default_approval
        if tool.approve_every_call and policy in {ToolApprovalPolicy.ONCE_PER_RUN, ToolApprovalPolicy.ONCE_PER_THREAD}:
            return ToolApprovalPolicy.EVERY_CALL
        return policy

    @staticmethod
    async def needs_approval(
        tool: DeclaredTool, config: ToolLoopConfig, run_context: RunContext, thread_context: ThreadContext
    ) -> bool:
        match ToolApprovals.policy(tool, config):
            case ToolApprovalPolicy.NEVER:
                return False
            case ToolApprovalPolicy.ONCE_PER_RUN:
                return not await run_context.get(ToolApprovals._key(tool.name), False)
            case ToolApprovalPolicy.ONCE_PER_THREAD:
                return not await thread_context.get(ToolApprovals._key(tool.name), False)
        return True

    @staticmethod
    async def remember(
        tool: DeclaredTool, config: ToolLoopConfig, run_context: RunContext, thread_context: ThreadContext
    ) -> None:
        match ToolApprovals.policy(tool, config):
            case ToolApprovalPolicy.ONCE_PER_RUN:
                await run_context.set(ToolApprovals._key(tool.name), True)
            case ToolApprovalPolicy.ONCE_PER_THREAD:
                await thread_context.set(ToolApprovals._key(tool.name), True)

    @staticmethod
    def _key(tool_name: str) -> str:
        return f"tool_loop:approved:{tool_name}"
