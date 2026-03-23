from fastapi import Request, WebSocket

from swiss_ai_hub.core.distributor.external_process_event_distributor import ExternalProcessEventDistributor


def use_external_process_event_distributor(request: Request) -> ExternalProcessEventDistributor:
    return request.app.state.external_process_event_distributor


def use_external_process_event_distributor_ws(request: WebSocket) -> ExternalProcessEventDistributor:
    return request.app.state.external_process_event_distributor
