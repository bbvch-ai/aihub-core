import asyncio
import os

from aihub_agent.agents.WebuiAgent.WebuiAgent import WebuiAgent
from aihub_agent.agents.WebuiAgent.WebuiAgentConfig import WebuiAgentConfig, WebuiFeatures
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=WebuiAgent,
        agent_config=WebuiAgentConfig(
            agent_id="deepseek",
            name=LocaleString(en="Webui Agent"),
            description=LocaleString(en="This is an agent that wraps an openai webui assistant"),
            system_prompt=LocaleString(en="You are an agent"),
            webui_base_url="http://localhost:8080",
            webui_bearer_token=os.environ.get("WEBUI_BEARER_TOKEN"),
            assistant_name="deepseek",
            features=WebuiFeatures(web_search=False),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
