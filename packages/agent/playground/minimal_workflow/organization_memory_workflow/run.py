# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgent import OrganizationMemoryAgent
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgentConfig import (
    OrganizationMemoryAgentConfig,
)

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=OrganizationMemoryAgent,
        agent_config=OrganizationMemoryAgentConfig(
            agent_class=OrganizationMemoryAgent.__name__,
            agent_id="org_memory_agent",
            name=LocaleString(en="Organization Memory Agent"),
            description=LocaleString(
                en="Agent for storing and retrieving explicit organizational facts shared across all users"
            ),
            llm=LLMConfig(
                model_name="text-generation/gpt-oss-120b",
                default_parameter=LLMParameter(temperature=1.0),
            ),
            tenant_id="default_tenant",
            tenant_namespace="default_namespace",
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
