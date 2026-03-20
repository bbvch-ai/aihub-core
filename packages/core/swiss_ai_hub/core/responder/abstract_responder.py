import abc
from collections.abc import Awaitable, Callable
from typing import Annotated, Literal, TypeVar

from nats.aio.client import Client as NATS
from pydantic import BaseModel

TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse", bound=BaseModel)


class AbstractResponder[TRequest: BaseModel, TResponse: BaseModel](abc.ABC):
    """
    Base class for NATS request-reply responders (servers).

    Listens on a subject and responds to incoming requests using a handler function.
    Similar to AbstractSubscriber but for request-reply pattern.

    ### Why AbstractResponder?
    - Type safety: Generic over TRequest and TResponse
    - Consistent naming: Follows {name}{protocol}Responder pattern
    - Lifecycle: start()/stop() methods for clean resource management
    - Tracing: OpenTelemetry integration

    ### Example Usage:
    ```python
    async def my_handler(request: MyRequest, subject: str) -> MyResponse:
        return MyResponse(result=process(request))

    responder = NCResponder[MyRequest, MyResponse](
        name="MyService",
        nc=nats_client,
        subject="my.subject.*",
        request_cls=MyRequest,
        handler=my_handler,
    )
    await responder.start()
    ```
    """

    def __init__(
        self,
        name: Annotated[str, "Name of the responder shown in otel"],
        nc: Annotated[NATS, "NATS client"],
        subject: Annotated[str, "NATS subject to listen on (supports wildcards)"],
        request_cls: Annotated[type[TRequest], "Request class for deserialization"],
        handler: Annotated[
            Callable[[TRequest, str], Awaitable[TResponse]],
            "Handler function: (request, subject) -> response",
        ],
        protocol: Annotated[Literal["NATS"], "Protocol (currently only NATS Core)"],
    ):
        self.name = name if name.endswith(f"{protocol}Responder") else f"{name}{protocol}Responder"
        self.nc = nc
        self.subject = subject
        self.request_cls = request_cls
        self.handler = handler

    @abc.abstractmethod
    async def start(self) -> None:
        """Start listening for requests."""
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        """Stop listening and clean up resources."""
        pass
