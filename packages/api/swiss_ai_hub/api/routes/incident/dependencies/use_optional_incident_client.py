from fastapi import Request

from swiss_ai_hub.api.routes.incident.github_issue_client import GitHubIssueClient


def use_optional_incident_client(request: Request) -> GitHubIssueClient | None:
    """The issue client if the deployment configured one, else None — for the endpoint that reports which it is."""
    return getattr(request.app.state, "incident_client", None)
