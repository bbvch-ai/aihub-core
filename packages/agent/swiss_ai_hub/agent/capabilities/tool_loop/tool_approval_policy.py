from enum import StrEnum


class ToolApprovalPolicy(StrEnum):
    """When the user must approve a tool call before it runs.

    A remembered approval covers the tool, not one set of arguments, unless the tool asks for every call to be
    approved: approving code execution once must not approve whatever code comes next.
    """

    NEVER = "never"
    EVERY_CALL = "every_call"
    ONCE_PER_RUN = "once_per_run"
    ONCE_PER_THREAD = "once_per_thread"
