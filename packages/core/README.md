# Swiss AI Hub Core

Foundational shared library for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) platform — an open-source,
self-hosted AI platform for enterprises. `swiss-ai-hub-core` provides the infrastructure every other Swiss AI Hub
package builds on:

- **Swiss AI Agent Protocol** — event-driven messaging over NATS with a strict Control Event (workflow) vs Display Event
  (observability) separation, hierarchical topic scoping, publishers/subscribers, and RPC.
- **Authentication & authorization** — identity models, Keycloak/OIDC handlers, and a hierarchical permission engine.
- **AI/ML utilities** — retrieval, reranking, guards, memory, document parsing, and the Form duality system.

## Installation

```bash
pip install swiss-ai-hub-core
```

## Usage

```python
from swiss_ai_hub.core.events.agent import StartEvent, ChunkEvent
from swiss_ai_hub.core.form import Form
```

`swiss_ai_hub` is a
[native namespace package](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/). Other
distributions (`swiss-ai-hub-agent`, `swiss-ai-hub-api`, …) contribute sibling modules under the same `swiss_ai_hub.*`
namespace.

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
