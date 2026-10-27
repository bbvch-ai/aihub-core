from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.jira.jira_authentication_error import JiraAuthenticationError
    from swiss_ai_hub.core.jira.jira_client import JiraClient
    from swiss_ai_hub.core.jira.jira_configuration_error import JiraConfigurationError
    from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig, JiraDeployment
    from swiss_ai_hub.core.jira.jira_error import JiraError
    from swiss_ai_hub.core.jira.jira_html import JiraHtml
    from swiss_ai_hub.core.jira.jira_invalid_query_error import JiraInvalidQueryError
    from swiss_ai_hub.core.jira.jira_jql import JiraJql
    from swiss_ai_hub.core.jira.jira_project_not_found_error import JiraProjectNotFoundError
    from swiss_ai_hub.core.jira.jira_request_error import JiraRequestError
    from swiss_ai_hub.core.jira.jira_ticket import JiraTicket
    from swiss_ai_hub.core.jira.jira_ticket_search import JiraTicketSearch
    from swiss_ai_hub.core.jira.jira_too_many_tickets_error import JiraTooManyTicketsError
    from swiss_ai_hub.core.jira.jira_version import JiraVersion

__all__ = [
    "JiraAuthenticationError",
    "JiraClient",
    "JiraConfigurationError",
    "JiraConnectionConfig",
    "JiraDeployment",
    "JiraError",
    "JiraHtml",
    "JiraInvalidQueryError",
    "JiraJql",
    "JiraProjectNotFoundError",
    "JiraRequestError",
    "JiraTicket",
    "JiraTicketSearch",
    "JiraTooManyTicketsError",
    "JiraVersion",
]

_CONNECTION_CONFIG_MODULE = "swiss_ai_hub.core.jira.jira_connection_config"

_LAZY_IMPORTS = {
    "JiraAuthenticationError": "swiss_ai_hub.core.jira.jira_authentication_error",
    "JiraClient": "swiss_ai_hub.core.jira.jira_client",
    "JiraConfigurationError": "swiss_ai_hub.core.jira.jira_configuration_error",
    "JiraConnectionConfig": _CONNECTION_CONFIG_MODULE,
    "JiraDeployment": _CONNECTION_CONFIG_MODULE,
    "JiraError": "swiss_ai_hub.core.jira.jira_error",
    "JiraHtml": "swiss_ai_hub.core.jira.jira_html",
    "JiraInvalidQueryError": "swiss_ai_hub.core.jira.jira_invalid_query_error",
    "JiraJql": "swiss_ai_hub.core.jira.jira_jql",
    "JiraProjectNotFoundError": "swiss_ai_hub.core.jira.jira_project_not_found_error",
    "JiraRequestError": "swiss_ai_hub.core.jira.jira_request_error",
    "JiraTicket": "swiss_ai_hub.core.jira.jira_ticket",
    "JiraTicketSearch": "swiss_ai_hub.core.jira.jira_ticket_search",
    "JiraTooManyTicketsError": "swiss_ai_hub.core.jira.jira_too_many_tickets_error",
    "JiraVersion": "swiss_ai_hub.core.jira.jira_version",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
