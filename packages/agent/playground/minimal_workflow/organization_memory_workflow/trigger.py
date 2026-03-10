import asyncio

from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events import UserMessageEvent

from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgent import OrganizationMemoryAgent
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgentConfig import (
    OrganizationMemoryAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    """One-shot test runner for OrganizationMemoryAgent."""
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
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
