import re
from typing import Annotated

from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.rpc import CallableAgent
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.capabilities.agent_tools.agent_tools_config import AgentToolsConfig
from swiss_ai_hub.agent.capabilities.agent_tools.offered_agent import OfferedAgent
from swiss_ai_hub.agent.context.run.run_context import RunContext

TOOL_NAME_LIMIT = 64


class OfferedAgents:
    """
    The agents a run offers its model, chosen once per run and kept in the run context.

    A call is resolved against this record only, never against the name the model wrote, so the model cannot reach
    an agent it was not offered: one the user may not use, the asking agent itself, or one the profile leaves out.
    """

    _KEY = "agent_tools:offered"

    @staticmethod
    def choose(
        online: Annotated[list[CallableAgent], "Every online agent profile"],
        config: AgentToolsConfig,
        access: AccessChecker,
        caller: Annotated[AgentInstanceTopic | None, "The asking run, never offered to itself"],
        family: Annotated[str, "The tool family's name, the prefix of every tool"],
    ) -> list[tuple[OfferedAgent, CallableAgent]]:
        chosen: list[tuple[OfferedAgent, CallableAgent]] = []
        taken: set[str] = set()
        for agent in sorted(online, key=lambda candidate: (candidate.agent_class, candidate.agent_id)):
            if not agent.is_conversational or not config.admits(agent.agent_class, agent.agent_id):
                continue
            if caller and (agent.agent_class, agent.agent_id) == (caller.agent_class, caller.agent_id):
                continue
            if not access.has_access_to_agent(agent.agent_class, agent.agent_id):
                continue
            tool_name = OfferedAgents._tool_name(family, agent.agent_id, taken)
            taken.add(tool_name)
            offered = OfferedAgent(
                tool_name=tool_name,
                agent_class=agent.agent_class,
                agent_id=agent.agent_id,
                name=agent.name,
                approval=config.approval_for(agent.agent_class, agent.agent_id),
            )
            chosen.append((offered, agent))
        return chosen

    @staticmethod
    async def keep(offered: list[OfferedAgent], run_context: RunContext) -> None:
        await run_context.set(OfferedAgents._KEY, {agent.tool_name: agent.model_dump(mode="json") for agent in offered})

    @staticmethod
    async def find(tool_name: str, run_context: RunContext) -> OfferedAgent | None:
        offered = (await run_context.get(OfferedAgents._KEY, {})).get(tool_name)
        return OfferedAgent.model_validate(offered) if offered else None

    @staticmethod
    def _tool_name(family: str, agent_id: str, taken: set[str]) -> str:
        """`{family}__{agent_id}` within the 64 characters a tool name may have; a suffix tells same ids apart."""
        stem = f"{family}__{re.sub(r'[^a-zA-Z0-9_-]', '_', agent_id)}"[:TOOL_NAME_LIMIT]
        name, counter = stem, 2
        while name in taken:
            suffix = f"_{counter}"
            name, counter = stem[: TOOL_NAME_LIMIT - len(suffix)] + suffix, counter + 1
        return name
