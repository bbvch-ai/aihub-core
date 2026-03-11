from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig

from .structured_data_extractor import TEMPLATE as STRUCTURED_DATA_EXTRACTOR
from .support_ticket_classifier import TEMPLATE as SUPPORT_TICKET_CLASSIFIER
from .tone_rewriter import TEMPLATE as TONE_REWRITER

ALL_TEMPLATES: list[FewShotAgentConfig] = [
    SUPPORT_TICKET_CLASSIFIER,
    STRUCTURED_DATA_EXTRACTOR,
    TONE_REWRITER,
]
