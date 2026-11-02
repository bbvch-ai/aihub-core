# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.code_execution_workflow.code_execution_playground_config import (
    CodeExecutionPlaygroundConfig,
)
from playground.minimal_workflow.code_execution_workflow.python_block_agent import PythonBlockAgent
from swiss_ai_hub.agent.runners import AgentRunner

enable_logging()


async def main():
    """The deterministic code-execution blueprint, for an OpenWebUI chat to send Python blocks to."""
    await AgentRunner(
        agent_type=PythonBlockAgent, agent_config=CodeExecutionPlaygroundConfig.as_form(), health_port=8097
    ).run_forever()


if __name__ == "__main__":
    asyncio.run(main())
