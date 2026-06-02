# Swiss AI Hub API

REST API, WebSocket gateway, and MCP server for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) platform.
Built on FastAPI, it bridges frontends and external clients to Swiss AI Hub services via the Swiss AI Agent Protocol.

- **Dynamic endpoints** — agent and process endpoints are registered at runtime from NATS discovery, not hardcoded.
- **Real-time** — WebSocket and OpenAI-compatible SSE streaming of agent display events.
- **Importable** — mount any subset of controllers on an `ApiRunner` to build your own API.

## Installation

```bash
pip install swiss-ai-hub-api
```

This pulls in [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/).

## Usage

```python
from swiss_ai_hub.api.routes.agent import AgentController
```

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
