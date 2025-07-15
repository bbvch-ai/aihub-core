from fastapi import Request, WebSocket

from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor


def use_external_process_event_distributor(request: Request) -> ExternalProcessEventDistributor:
    return request.app.state.external_process_event_distributor


def use_external_process_event_distributor_ws(request: WebSocket) -> ExternalProcessEventDistributor:
    return request.app.state.external_process_event_distributor
