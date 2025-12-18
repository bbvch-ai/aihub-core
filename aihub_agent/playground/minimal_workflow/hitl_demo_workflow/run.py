import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.hitl_demo_workflow.HitlDemoAgent import HitlDemoAgent
from playground.minimal_workflow.hitl_demo_workflow.HitlDemoAgentConfig import HitlDemoAgentConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=HitlDemoAgent,
        default_agent_config=HitlDemoAgentConfig(
            agent_id="hitl_demo_agent",
            agent_class=HitlDemoAgent.__name__,
            name=LocaleString(en="HITL Demo Agent"),
            description=LocaleString(en="Demo agent showcasing all HITL types"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
