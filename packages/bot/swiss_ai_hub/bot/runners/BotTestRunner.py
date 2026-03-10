from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse

from swiss_ai_hub.bot.runners.BotRunner import BotRunner


@dataclass
class BotServiceResponse:
    path: str
    payload: dict


class BotTestRunner(BotRunner):
    def __init__(self, conversation_ttl_days: float = 30):
        super().__init__(
            title="Local AI Hub Bot Service",
            description="Local version only",
            origins=[],
            conversation_ttl_days=conversation_ttl_days,
        )

        self._api_app.add_api_route(
            "/service{full_path:path}",
            self.service_endpoint,
            methods=["POST", "PUT"],
            summary="Catch-all service endpoint for bot responses",
        )

        self.responses: list[BotServiceResponse] = []

    async def service_endpoint(self, request: Request, full_path: str):
        """
        This endpoint catches POST requests to any URL that starts with /service.
        The 'full_path' parameter contains the remaining path after /service.
        """
        print("Connection received")
        payload = await request.json()
        self.responses.append(BotServiceResponse(path=full_path, payload=payload))
        return JSONResponse({"id": payload.get("id") or "test_id"})

    async def run(self) -> None:
        """
        Start the uvicorn server on localhost:8001 with debug logging enabled.

        This should be called from an async context, e.g., using `asyncio.run(runner.run())`.
        """
        from uvicorn import Config, Server

        config = Config(app=self.create_app(), host="localhost", port=8001, log_level="debug")
        server = Server(config)
        await server.serve()
