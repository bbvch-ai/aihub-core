from swiss_ai_hub.agent.agents.web_fetch_agent import WebFetchAgentConfig


def get_all_templates() -> list[WebFetchAgentConfig]:
    from .article_summariser import build as build_article_summariser
    from .page_comparison import build as build_page_comparison

    return [
        build_article_summariser(),
        build_page_comparison(),
    ]
