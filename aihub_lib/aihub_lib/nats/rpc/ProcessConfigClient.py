from typing import Annotated, Any

from nats.aio.client import Client as NATS

from aihub_lib.nats.requester.NCRequester import NCRequester
from aihub_lib.nats.rpc.models import FetchProcessConfigRequest, FetchProcessConfigResponse
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager


class ProcessConfigClient:
    """
    High-level client for fetching process configurations via NATS RPC.

    This client provides a simple interface for processes to fetch their configurations
    from the API service at runtime, decoupling config management from event payloads.

    ### Example Usage:
    ```python
    client = ProcessConfigClient(nc)
    config = await client.fetch_config("OnboardingProcess", "hr-onboarding")
    ```

    ### Subject Pattern:
    Requests are sent to: `aihub.rpc.config.process.{process_class}.{process_id}`
    (managed by ProcessTopicManager.get_process_config_rpc_subject)
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client"],
        timeout_ms: Annotated[int, "Request timeout in milliseconds"] = 5000,
    ):
        self._requester: NCRequester[FetchProcessConfigRequest, FetchProcessConfigResponse] = NCRequester(
            name="ProcessConfig",
            nc=nc,
            response_cls=FetchProcessConfigResponse,
            default_timeout_ms=timeout_ms,
        )
        self._topic_manager = ProcessTopicManager()

    async def fetch_config(
        self,
        process_class: str,
        process_id: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """
        Fetch configuration for a process instance.
        """
        subject = self._topic_manager.get_process_config_rpc_subject(process_class, process_id)

        response = await self._requester.request(
            FetchProcessConfigRequest(process_class=process_class, process_id=process_id),
            subject=subject,
            timeout_ms=timeout_ms,
        )

        if not response.found:
            raise ValueError(f"Config not found for {process_class}/{process_id}: {response.error}")

        return response.config
