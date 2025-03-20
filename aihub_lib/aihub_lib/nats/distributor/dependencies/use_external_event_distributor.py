from fastapi import Request

from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor


def use_external_event_distributor(request: Request) -> ExternalEventDistributor:
    return request.app.state.external_event_distributor
