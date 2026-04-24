from swiss_ai_hub.agent.agents.few_shot_agent import FewShotAgentConfig


def get_all_templates() -> list[FewShotAgentConfig]:
    from .structured_data_extractor import build as build_structured_data_extractor
    from .support_ticket_classifier import build as build_support_ticket_classifier
    from .tone_rewriter import build as build_tone_rewriter

    return [
        build_support_ticket_classifier(),
        build_structured_data_extractor(),
        build_tone_rewriter(),
    ]
