from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from pydantic import Field


class ExpertAskingAgentConfig(AgentConfig):
    llm: LLMConfig
    slack_channel_id: Annotated[
        str, Field(..., description="Slack channel ID to which expert question should be posted")
    ]
    loop_max: Annotated[int, Field(3, description="Maximum number of loops to ask experts", gt=0)]
    open_webui_knowledge_id: Annotated[str, Field(..., description="Knowledge ID for Open WebUI")]
    open_webui_api_key: Annotated[str, Field(..., description="API key for Open WebUI")]
    open_webui_api_url: Annotated[str, Field(..., description="API URL for Open WebUI")]
