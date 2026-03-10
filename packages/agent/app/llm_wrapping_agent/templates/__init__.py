from swiss_ai_hub.agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig

from .code_explainer import TEMPLATE as CODE_EXPLAINER
from .email_drafter import TEMPLATE as EMAIL_DRAFTER
from .meeting_minutes import TEMPLATE as MEETING_MINUTES

ALL_TEMPLATES: list[LLMWrappingAgentConfig] = [
    MEETING_MINUTES,
    EMAIL_DRAFTER,
    CODE_EXPLAINER,
]
