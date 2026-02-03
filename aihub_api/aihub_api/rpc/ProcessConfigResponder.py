"""
NATS RPC responder for process configuration requests.

This module provides a responder that allows processes to fetch their configurations
at runtime via NATS request-reply, decoupling config management from event payloads.
"""

import logging
from typing import Annotated

from aihub_lib.nats.responder.NCResponder import NCResponder
from aihub_lib.nats.rpc.models import FetchProcessConfigRequest, FetchProcessConfigResponse
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from nats.aio.client import Client as NATS

from aihub_api.routes.process.ProcessService import ProcessService

logger = logging.getLogger(__name__)


class ProcessConfigResponder:
    """
    NATS RPC responder for process configuration requests.

    Listens on `aihub.rpc.config.process.*.*` and responds with process configurations
    fetched from the database.

    Subject pattern is managed by ProcessTopicManager.get_process_config_rpc_subject().

    ### Example Usage:
    ```python
    responder = ProcessConfigResponder(nc)
    await responder.start()
    # ... on shutdown
    await responder.stop()
    ```
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client"],
    ):
        self._topic_manager = ProcessTopicManager()
        self._subject = self._topic_manager.get_process_config_rpc_subject("*", "*")
        self._responder: NCResponder[FetchProcessConfigRequest, FetchProcessConfigResponse] = NCResponder(
            name="ProcessConfig",
            nc=nc,
            subject=self._subject,
            request_cls=FetchProcessConfigRequest,
            handler=self._handle_request,
        )

    async def start(self) -> None:
        """Start listening for process config requests."""
        logger.info(f"ProcessConfigResponder starting on {self._subject}")
        await self._responder.start()

    async def stop(self) -> None:
        """Stop listening for requests."""
        logger.info("ProcessConfigResponder stopping")
        await self._responder.stop()

    async def _handle_request(
        self,
        request: FetchProcessConfigRequest,
        subject: str,
    ) -> FetchProcessConfigResponse:
        """
        Handle a config fetch request by looking up the process's configuration.
        """
        logger.debug(f"Handling config request for {request.process_class}/{request.process_id}")

        try:
            config = await ProcessService.get_process_configuration(
                process_class=request.process_class,
                process_id=request.process_id,
            )

            return FetchProcessConfigResponse(
                process_class=request.process_class,
                process_id=request.process_id,
                config=config,
                found=True,
            )

        except Exception as e:
            logger.exception(f"Error fetching config for {request.process_class}/{request.process_id}: {e}")
            return FetchProcessConfigResponse(
                process_class=request.process_class,
                process_id=request.process_id,
                config={},
                found=False,
                error=str(e),
            )
