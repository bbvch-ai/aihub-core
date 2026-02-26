from fastapi import Request

from aihub_api.routes.agent.AgentFileUploadService import AgentFileUploadService


def use_agent_file_upload_service(request: Request) -> AgentFileUploadService:
    """FastAPI dependency that provides the singleton agent file upload service."""
    return request.app.state.agent_file_upload_service
