import logging

from api_core.runners.ApiRunner import ApiRunner



class ApiTestRuner(ApiRunner):

    def __init__(self):
        super().__init__(title="Local AI Hub", description="Local version only", origins=[], debug=True)

    async def run(self) -> None:
        from uvicorn import Config, Server

        config = Config(app=self.app, host="localhost", port=8000, log_level="debug")
        server = Server(config)
        await server.serve()

