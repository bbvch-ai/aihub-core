<div align="center">

# swiss-ai-hub-process

**The process-orchestration SDK for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) — coordinate agents, humans,
and programs in multi-step business processes.**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-process?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-process/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-process?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-process/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/process/LICENSE)
[![Status](https://img.shields.io/badge/status-experimental%20%C2%B7%20WIP-orange?style=flat-square)](#status)

</div>

______________________________________________________________________

> ## ⚠️ Status
>
> **This package is experimental and a work in progress.** Its APIs are unstable and likely to change, it is not yet
> production-ready, and it has no production entry point. Use it for exploration only — don't build on it yet.

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. You
build agents, pipelines, and processes with the Python SDK; the platform provides the runtime.

## What is this package?

`swiss-ai-hub-process` is an SDK for orchestrating **multi-entity processes** — workflows that delegate work across four
kinds of participant: **agents**, **humans**, **programs**, and other **processes**. A process never does the work
itself; it routes work between entities. Each step declares an `In` (where work arrives from) and an `Out` (where it's
delegated to):

```python
from swiss_ai_hub.process import AgenticProcess, process_step, Agent, Human

class ReviewProcess(AgenticProcess):
    @process_step()
    def analyze(self, work: ...) -> ...:        # delegate to an Agent, then a Human reviews, ...
        ...
```

It builds on [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/) and the same decentralized workflow
engine as [`swiss-ai-hub-agent`](https://pypi.org/project/swiss-ai-hub-agent/).

## Installation

```bash
pip install swiss-ai-hub-process
```

Requires **Python 3.13**.

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/
- **The full SDK** (meta package): https://pypi.org/project/swiss-ai-hub/

## License

Apache-2.0 — see [packages/process/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/process/LICENSE).
For the full per-package license matrix, see
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
