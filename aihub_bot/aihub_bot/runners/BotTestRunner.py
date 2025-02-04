from dataclasses import dataclass
from typing import Dict, List

from fastapi import Request
from fastapi.responses import JSONResponse

from aihub_bot.runners.BotRunner import BotRunner


@dataclass
class BotServiceResponse:
    path: str
    payload: Dict


class BotTestRunner(BotRunner):
    def __init__(self):
        super().__init__(title="Local AI Hub Bot Service", description="Local version only", origins=[], debug=True)

        # This is the base service URL you'll provide to the bot.
        self.service_url = "http://localhost:8001/service"

        # Register a route that catches all POST requests to /service and any sub-URLs.
        # The wildcard "{full_path:path}" will capture any additional path segments.
        self._base_app.add_api_route(
            "/service{full_path:path}",
            self.service_endpoint,
            methods=["POST"],
            summary="Catch-all service endpoint for bot responses",
        )

        self.responses: List[BotServiceResponse] = []

    async def service_endpoint(self, request: Request, full_path: str):
        """
        This endpoint catches POST requests to any URL that starts with /service.
        The 'full_path' parameter contains the remaining path after /service.
        """
        payload = await request.json()
        # You can log or store the payload for later inspection during testing.
        self.responses.append(BotServiceResponse(path=full_path, payload=payload))

        # Respond with a simple acknowledgment.
        return JSONResponse({"status": "received", "path": full_path})

    async def run(self) -> None:
        """
        Start the uvicorn server on localhost:8001 with debug logging enabled.

        This should be called from an async context, e.g., using `asyncio.run(runner.run())`.
        """
        from uvicorn import Config, Server

        config = Config(app=self._base_app, host="localhost", port=8001, log_level="debug")
        server = Server(config)
        await server.serve()
