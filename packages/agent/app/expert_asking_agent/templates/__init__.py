from swiss_ai_hub.agent.agents.expert_asking_agent import ExpertAskingAgentConfig


def get_all_templates() -> list[ExpertAskingAgentConfig]:
    from .engineering_expert import build as build_engineering_expert

    return [
        build_engineering_expert(),
    ]
