from fastapi import Request, WebSocket


from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor


def use_external_event_distributor(request: Request) -> ExternalEventDistributor:
    return request.app.state.external_event_distributor

def use_external_event_distributor_ws(request: WebSocket) -> ExternalEventDistributor:
    return request.app.state.external_event_distributor