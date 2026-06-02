# Swiss AI Hub

Meta-package for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) Python SDK. Installing it pulls in the full
SDK in one step:

| Package                                                                    | Import                  | Purpose                                         |
| -------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------- |
| [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/)         | `swiss_ai_hub.core`     | Shared infrastructure & Swiss AI Agent Protocol |
| [`swiss-ai-hub-agent`](https://pypi.org/project/swiss-ai-hub-agent/)       | `swiss_ai_hub.agent`    | Build workflow-based AI agents                  |
| [`swiss-ai-hub-api`](https://pypi.org/project/swiss-ai-hub-api/)           | `swiss_ai_hub.api`      | REST API + WebSocket gateway                    |
| [`swiss-ai-hub-bot`](https://pypi.org/project/swiss-ai-hub-bot/)           | `swiss_ai_hub.bot`      | Teams / Slack / web chat integrations           |
| [`swiss-ai-hub-pipeline`](https://pypi.org/project/swiss-ai-hub-pipeline/) | `swiss_ai_hub.pipeline` | Dagster ingestion pipelines                     |
| [`swiss-ai-hub-process`](https://pypi.org/project/swiss-ai-hub-process/)   | `swiss_ai_hub.process`  | Multi-entity process orchestration              |

## Installation

```bash
pip install swiss-ai-hub
```

Prefer a smaller footprint? Install only the packages you need — e.g. `pip install swiss-ai-hub-agent`.

The operational [`swiss-ai-hub-backup`](https://pypi.org/project/swiss-ai-hub-backup/) service (AGPL-3.0-or-later) is
**not** bundled here; install it separately if you need it.

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
