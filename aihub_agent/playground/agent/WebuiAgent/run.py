import asyncio

from aihub_agent.agents.webui.WebuiAgent.WebuiAgent import WebuiAgent
from aihub_agent.agents.webui.WebuiAgent.WebuiAgentConfig import WebuiAgentConfig, WebuiFeatures
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=WebuiAgent,
        agent_config=WebuiAgentConfig(
            agent_id="dev_agent",
            name=LocaleString(en="Dev Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            system_prompt=LocaleString(en="You are an agent"),
            webui_base_url="http://localhost:8080",
            webui_bearer_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjNkMzYyMjYwLTk5YzEtNDFjZC1hYmU4LTcyN2JhOWM2ZGFhMCJ9.dnIaLs4OdwQ6ZsEgKaWpNFeQyfOSHCIT2wu83ZeKZgE",
            assistant_name="deepseek",
            features=WebuiFeatures(web_search=False)
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
