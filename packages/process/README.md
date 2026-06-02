# Swiss AI Hub Process

Agentic process SDK for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) platform. Orchestrate multi-step
business processes that delegate work across agents, humans, programs, and other processes.

- **Entity delegation** — the core differentiator: each step declares `In`/`Out` entity annotations (Agent, Human,
  Program, Process) and the engine routes work between them.
- **Stateless orchestration** — built on the same decentralized `DispatchableWorkflow` engine as agents; state lives in
  Redis (`WalkthroughContext`) and the JetStream event history.
- **Human + AI + systems** — combine LLM agents, human approval forms, and external program calls in one process.

## Installation

```bash
pip install swiss-ai-hub-process
```

This pulls in [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/).

## Usage

```python
from swiss_ai_hub.process import AgenticProcess, ProcessRunner
```

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
