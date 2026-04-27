from swiss_ai_hub.agent.agents.llm_wrapping_agent import LLMWrappingAgentConfig


def get_all_templates() -> list[LLMWrappingAgentConfig]:
    from .code_explainer import build as build_code_explainer
    from .email_drafter import build as build_email_drafter
    from .meeting_minutes import build as build_meeting_minutes

    return [
        build_meeting_minutes(),
        build_email_drafter(),
        build_code_explainer(),
    ]
