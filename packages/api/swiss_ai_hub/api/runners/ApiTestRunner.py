from swiss_ai_hub.api.runners.ApiRunner import ApiRunner


class ApiTestRunner(ApiRunner):
    """
    A specialized runner for local testing and development of the AI Hub API.

    ### Why ApiTestRunner?
    When developing locally, you may need a version of the API that:
    - Uses debug mode for verbose logging.
    - Restricts origins to a controlled list (or none).
    - Runs on a standard localhost address and port.

    `ApiTestRunner` provides these defaults, ensuring a simple and convenient environment for
    local testing, debugging, or rapid iteration without deploying to production.

    ### Features
    - Sets the application title to "Local AI Hub" and description to "Local version only".
    - Explicitly configures empty `origins=[]` for CORS, suitable for a tightly controlled local setup.
    - Enables debug mode for detailed log outputs.
    - Provides a `run` method to start a uvicorn server on `localhost:8000`.

    ### Usage
    ```python
    runner = ApiTestRunner()
    runner.mount(MyController())
    await runner.run()
    ```

    This starts a development server with debug logs, ideal for local testing.
    """

    def __init__(self):
        super().__init__(title="Local AI Hub", description="Local version only", origins=[])

    async def run(self) -> None:
        """
        Start the uvicorn server on localhost:8000 with debug logging enabled.

        This should be called from an async context, e.g., using `asyncio.run(runner.run())`.
        """
        from uvicorn import Config, Server

        config = Config(app=self.create_app(), host="localhost", port=8000, log_level="debug")
        server = Server(config)
        await server.serve()
