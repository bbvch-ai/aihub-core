from swiss_ai_hub.core.auth import UserIdentity

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext


class ToolApprovals:
    """Which calls need the user's approval, and which approvals the user already gave for the run or conversation."""

    @staticmethod
    def policy(name: str, options: ToolOptions, config: ToolLoopConfig) -> ToolApprovalPolicy:
        """The profile's rule, else the tool's default; a tool approved per call never lets an approval carry over."""
        rule = config.approval_rule_for(name)
        policy = ToolApprovalPolicy(rule.policy) if rule else options.default_approval
        if options.approve_every_call and policy in {
            ToolApprovalPolicy.ONCE_PER_RUN,
            ToolApprovalPolicy.ONCE_PER_THREAD,
        }:
            return ToolApprovalPolicy.EVERY_CALL
        return policy

    @staticmethod
    async def needs_approval(
        name: str,
        options: ToolOptions,
        config: ToolLoopConfig,
        run_context: RunContext,
        thread_context: ThreadContext,
        user: UserIdentity | None,
    ) -> bool:
        match ToolApprovals.policy(name, options, config):
            case ToolApprovalPolicy.NEVER:
                return False
            case ToolApprovalPolicy.ONCE_PER_RUN:
                return not await run_context.get(ToolApprovals._key(name), False)
            case ToolApprovalPolicy.ONCE_PER_THREAD:
                return not await thread_context.get(ToolApprovals._thread_key(name, user), False)
        return True

    @staticmethod
    async def remember(
        name: str,
        options: ToolOptions,
        config: ToolLoopConfig,
        run_context: RunContext,
        thread_context: ThreadContext,
        user: UserIdentity | None,
    ) -> None:
        match ToolApprovals.policy(name, options, config):
            case ToolApprovalPolicy.ONCE_PER_RUN:
                await run_context.set(ToolApprovals._key(name), True)
            case ToolApprovalPolicy.ONCE_PER_THREAD:
                await thread_context.set(ToolApprovals._thread_key(name, user), True)

    @staticmethod
    def remembered_approver(
        name: str, options: ToolOptions, config: ToolLoopConfig, user: UserIdentity | None
    ) -> str | None:
        """Who approved a call that runs without asking: the run's user when an approval of theirs carried over, since
        approvals are remembered per run and per user; nobody for a tool that never asks."""
        if user is None or ToolApprovals.policy(name, options, config) == ToolApprovalPolicy.NEVER:
            return None
        return user.id

    @staticmethod
    def _key(tool_name: str) -> str:
        return f"tool_loop:approved:{tool_name}"

    @staticmethod
    def _thread_key(tool_name: str, user: UserIdentity | None) -> str:
        """Per user, since one member's approval must not run tools in another member's runs of a shared thread."""
        key = ToolApprovals._key(tool_name)
        return f"{key}:{user.id}" if user else key
