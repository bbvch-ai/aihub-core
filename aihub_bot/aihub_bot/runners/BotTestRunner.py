from aihub_bot.runners.BotRunner import BotRunner


class BotTestRunner(BotRunner):

    def __init__(self):
        super().__init__(title="Local AI Hub", description="Local version only", origins=[], debug=True)

    async def run(self) -> None:
        """
        Start the uvicorn server on localhost:8001 with debug logging enabled.

        This should be called from an async context, e.g., using `asyncio.run(runner.run())`.
        """
        from uvicorn import Config, Server

        config = Config(app=self._base_app, host="localhost", port=8001, log_level="debug")
        server = Server(config)
        await server.serve()
