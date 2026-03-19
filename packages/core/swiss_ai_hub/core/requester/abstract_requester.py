import abc
from typing import Annotated, Literal, TypeVar

from pydantic import BaseModel

TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse", bound=BaseModel)


class AbstractRequester[TRequest: BaseModel, TResponse: BaseModel](abc.ABC):
    """
    Base class for NATS request-reply clients.

    Provides typed request-response pattern over NATS, similar to how
    AbstractPublisher provides typed event publishing.

    ### Why AbstractRequester?
    - Type safety: Generic over TRequest and TResponse
    - Consistent naming: Follows {name}{protocol}Requester pattern
    - Tracing: OpenTelemetry integration
    - Timeout handling: Configurable request timeouts

    ### Example Usage:
    ```python
    requester = NCRequester[MyRequest, MyResponse](
        name="MyService",
        nc=nats_client,
        response_cls=MyResponse,
    )
    response = await requester.request(MyRequest(...), subject="my.subject")
    ```
    """

    def __init__(
        self,
        name: Annotated[str, "Name of the requester shown in otel"],
        response_cls: Annotated[type[TResponse], "Response class for deserialization"],
        protocol: Annotated[Literal["NATS"], "Protocol (currently only NATS Core)"],
        default_timeout_ms: Annotated[int, "Default timeout in milliseconds"] = 5000,
    ):
        self.name = name if name.endswith(f"{protocol}Requester") else f"{name}{protocol}Requester"
        self.response_cls = response_cls
        self.default_timeout_ms = default_timeout_ms

    @abc.abstractmethod
    async def request(
        self,
        request: TRequest,
        subject: str,
        timeout_ms: int | None = None,
    ) -> TResponse:
        """
        Send a request and wait for a response.
        """
        pass
