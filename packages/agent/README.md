# Swiss AI Hub Agent

Agent SDK for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) platform. Build transparent, workflow-based,
event-driven AI agents that run as independent microservices over NATS/JetStream.

- **Custom workflow engine** — define steps with `@step()`; inputs and outputs are inferred from event type annotations
  and dispatched via NATS, so consecutive steps can execute on different servers.
- **Stateless & decentralized** — all state lives in Redis (`RunContext`/`ThreadContext`) and the JetStream event
  history; agents scale horizontally.
- **Batteries included** — config with Form duality, dependency injection, i18n, memory, LLM streaming, and a catalog of
  pre-built agents (RAG, expert-asking, few-shot, …).

## Installation

```bash
pip install swiss-ai-hub-agent
```

This pulls in [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/).

## Usage

```python
from swiss_ai_hub.agent import Agent, AgentRunner
```

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
