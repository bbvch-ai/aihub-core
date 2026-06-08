<div align="center">

# swiss-ai-hub-core

**The foundational shared library for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Every other Swiss AI Hub
Python package depends on it — you rarely install it directly.**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-core?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-core/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-core?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-core/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/core/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers — LLM gateway (LiteLLM), vector search (Milvus), data pipelines
(Dagster), SSO (Keycloak), observability (Langfuse), a chat UI (Open-WebUI), and more. You build custom agents,
pipelines, processes, and bot integrations with the Python SDK; the platform provides the runtime.

## What is this package?

`swiss-ai-hub-core` is the shared foundation the rest of the SDK is built on. It is a **library, not a runnable
service** — it provides the **Swiss AI Agent Protocol** (typed, event-driven messaging over NATS), authentication &
multi-tenancy, the Form configuration system, and shared AI/ML utilities. Every higher-level package imports it.

## You usually don't install this directly

Install the package for **what you're building** — each one depends on `swiss-ai-hub-core` and pulls it in
automatically:

| You want to…                                   | Install                                                                    | Imports as               |
| ---------------------------------------------- | -------------------------------------------------------------------------- | ------------------------ |
| Build a workflow-based **AI agent**            | [`swiss-ai-hub-agent`](https://pypi.org/project/swiss-ai-hub-agent/)       | `swiss_ai_hub.agent`     |
| Expose a **REST API + WebSocket gateway**      | [`swiss-ai-hub-api`](https://pypi.org/project/swiss-ai-hub-api/)           | `swiss_ai_hub.api`       |
| Connect agents to **Teams / Slack / web chat** | [`swiss-ai-hub-bot`](https://pypi.org/project/swiss-ai-hub-bot/)           | `swiss_ai_hub.bot`       |
| Build a **document-ingestion pipeline**        | [`swiss-ai-hub-pipeline`](https://pypi.org/project/swiss-ai-hub-pipeline/) | `swiss_ai_hub.pipeline`  |
| Orchestrate **multi-entity processes**         | [`swiss-ai-hub-process`](https://pypi.org/project/swiss-ai-hub-process/)   | `swiss_ai_hub.process`   |
| Install **the whole SDK**                      | [`swiss-ai-hub`](https://pypi.org/project/swiss-ai-hub/) (meta)            | (pulls all of the above) |

Reach for `swiss-ai-hub-core` on its own only in the rare case where you're writing a service that speaks the Swiss AI
Agent Protocol directly, without one of the higher-level engines above.

## Installation

```bash
pip install swiss-ai-hub-core   # usually unnecessary — it comes in with the package you actually want
```

All distributions share the `swiss_ai_hub.*` [native (PEP 420) namespace](https://peps.python.org/pep-0420/), so
`swiss_ai_hub.core`, `swiss_ai_hub.agent`, … coexist as sibling modules regardless of which subset you install.

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0 — see [packages/core/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/core/LICENSE). For
the full per-package license matrix, see [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
