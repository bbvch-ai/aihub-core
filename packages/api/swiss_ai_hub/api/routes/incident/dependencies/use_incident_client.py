from fastapi import HTTPException, Request

from swiss_ai_hub.api.routes.incident.github_issue_client import GitHubIssueClient


def use_incident_client(request: Request) -> GitHubIssueClient:
    """Provides the singleton issue client, which caches its installation token.

    Absent when the deployment configured no incident repository — the endpoints are mounted
    regardless so the frontend gets a clear 404 instead of a route that does not exist.
    """
    client: GitHubIssueClient | None = getattr(request.app.state, "incident_client", None)
    if client is None:
        raise HTTPException(status_code=404, detail="Incident reporting is not configured on this deployment.")
    return client
