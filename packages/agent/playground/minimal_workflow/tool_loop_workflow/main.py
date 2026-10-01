# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from playground.minimal_workflow.tool_loop_workflow.answering_tool_loop_agent import AnsweringToolLoopAgent
from playground.minimal_workflow.tool_loop_workflow.gathering_tool_loop_agent import GatheringToolLoopAgent
from playground.minimal_workflow.tool_loop_workflow.tool_loop_playground_config import ToolLoopPlaygroundConfig
from swiss_ai_hub.core.infrastructure import enable_logging

from swiss_ai_hub.agent.runners import AgentRunner

enable_logging()


async def main():
    """Both playground blueprints, so an OpenWebUI chat can try the answering and the gathering loop."""
    await asyncio.gather(
        AgentRunner(
            agent_type=AnsweringToolLoopAgent, agent_config=ToolLoopPlaygroundConfig.as_form(), health_port=8095
        ).run_forever(),
        AgentRunner(
            agent_type=GatheringToolLoopAgent, agent_config=ToolLoopPlaygroundConfig.as_form(), health_port=8096
        ).run_forever(),
    )


if __name__ == "__main__":
    asyncio.run(main())
