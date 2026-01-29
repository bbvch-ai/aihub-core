# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgent import OrganizationMemoryAgent
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgentConfig import (
    OrganizationMemoryAgentConfig,
)

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=OrganizationMemoryAgent,
        default_agent_config=OrganizationMemoryAgentConfig(
            agent_class=OrganizationMemoryAgent.__name__,
            agent_id="org_memory_agent",
            name=LocaleString(en="Organization Memory Agent"),
            description=LocaleString(
                en="Agent for storing and retrieving explicit organizational facts shared across all users"
            ),
            llm=LLMConfig(model_name="text-generation/nano", default_parameter=LLMParameter(temperature=1.0)),
            tenant_id="default_tenant",
            tenant_namespace="default_namespace",
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
