from fastapi import Request, WebSocket

from swiss_ai_hub.core.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor


def use_external_agent_event_distributor(request: Request) -> ExternalAgentEventDistributor:
    return request.app.state.external_agent_event_distributor


def use_external_agent_event_distributor_ws(request: WebSocket) -> ExternalAgentEventDistributor:
    return request.app.state.external_agent_event_distributor
