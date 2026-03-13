# Rename and Restructure for Open-Source Release

## Context

Swiss AI Hub is preparing for its first public open-source release. The codebase had grown organically with internal
naming conventions that were never designed for public consumption. Several structural issues compounded over time:

**Flat, prefix-based repository layout.** All packages lived as top-level directories named with an `aihub_` prefix:
`aihub_lib/`, `aihub_agent/`, `aihub_api/`, `aihub_bot/`, `aihub_pipeline/`, `aihub_process/`, `swiss_ai_hub_web/`,
`aihub_doc/`, `aihub_action/`. Non-code directories (docs, CI actions) were mixed in at the same level with the same
prefix, making it hard to distinguish source packages from supporting infrastructure.

**CamelCase file and directory names.** The convention was one class per file, named after the class:
`ExpertAskingAgent/ExpertAskingAgent.py`, `FewShotAgent/FewShotAgentConfig.py`,
`NamespaceSelectionAgent/events/DetermineNamespacesEvent.py`. This created an import ambiguity: when an `__init__.py`
re-exported `ExpertAskingAgent`, Python could not distinguish whether `from ... import ExpertAskingAgent` referred to
the module `ExpertAskingAgent.py` or the class `ExpertAskingAgent` re-exported from `__init__.py`. This made introducing
proper `__init__.py`-based public interfaces impossible without renaming the files first.

**No public interface boundaries.** Without `__init__.py` exports, every package's internal file structure was its
public API. Any consumer could (and did) import directly from deeply nested module paths. Refactoring internal file
organization in one package would break imports across all other packages.

**Flat package names blocking namespace packages.** The import paths (`aihub_lib`, `aihub_agent`, etc.) were flat
top-level modules with no shared namespace. uv workspaces with `uv_build` support proper Python namespace packages
(`swiss_ai_hub.core`, `swiss_ai_hub.agent`), but this requires the source layout
`packages/<scope>/swiss_ai_hub/<scope>/` — a fundamentally different directory structure.

## Decision Drivers

- **Resolve CamelCase import ambiguity**\
  With CamelCase file names like `ExpertAskingAgent.py`, adding `__init__.py` files that export `ExpertAskingAgent`
  creates ambiguity: `from package import ExpertAskingAgent` could resolve to the module or the class. Renaming to
  `snake_case` (`expert_asking_agent.py`) eliminates this — `expert_asking_agent` (module) and `ExpertAskingAgent`
  (class) are syntactically distinct, allowing `__init__.py` files to work as intended.

- **Enable `__init__.py`-based public interfaces**\
  Without public interfaces, every internal file move is a cross-package breaking change. With lazy `__init__.py`
  exports (using `TYPE_CHECKING` + `__getattr__`), packages expose a curated set of symbols. Internal restructuring
  becomes invisible to consumers. Cross-package imports go through the interface; intra-package imports use full module
  paths.

- **Python namespace packages for publishable workspaces**\
  `uv_build` supports `module-name = "swiss_ai_hub.core"` in `pyproject.toml`, producing proper namespace packages where
  multiple independently installable packages share the `swiss_ai_hub` import prefix — the same pattern used by
  `google.cloud.*`, `azure.*`, and `aws_cdk.*`. This requires the source layout `packages/core/swiss_ai_hub/core/` with
  `module-root = ""`.

- **Standard monorepo layout**\
  Moving all source packages under `packages/` and non-code directories to conventional locations (`docs/`,
  `.github/actions/`, `infra/`) follows the standard monorepo pattern. The uv workspace `members` list becomes
  `["packages/core", "packages/agent", ...]` instead of mixing code and non-code directories at the root.

- **snake_case as Python standard**\
  PEP 8 prescribes `snake_case` for module names. CamelCase directories (`ExpertAskingAgent/`, `FewShotAgent/`) are
  non-standard in the Python ecosystem and cause friction with tools that expect lowercase module paths (linters, type
  checkers, import sorters).

- **Open-source brand identity**\
  `swiss-ai-hub-core` on PyPI and `@swiss-ai-hub/web` on npm are unambiguous and align with the project's positioning.
  Internal shorthand like `aihub_lib` communicates nothing to external users.

## Decision

We restructure the repository layout, rename all packages, and normalize file naming conventions.

### Repository layout

Top-level directories are reorganized by purpose:

| Before            | After                | Rationale                                            |
| ----------------- | -------------------- | ---------------------------------------------------- |
| `aihub_lib/`      | `packages/core/`     | Source packages grouped under `packages/`            |
| `aihub_agent/`    | `packages/agent/`    |                                                      |
| `aihub_api/`      | `packages/api/`      |                                                      |
| `aihub_bot/`      | `packages/bot/`      |                                                      |
| `aihub_pipeline/` | `packages/pipeline/` |                                                      |
| `aihub_process/`  | `packages/process/`  |                                                      |
| `swiss_ai_hub_web/`      | `packages/web/`      |                                                      |
| `aihub_doc/`      | `docs/`              | Standard documentation directory                     |
| `aihub_action/`   | `.github/actions/`   | GitHub's conventional location for composite actions |
| `deployment/`     | `infra/`             | Infrastructure and deployment config                 |

### Package naming and namespace structure

Each Python package is renamed to use the `swiss_ai_hub` namespace with `uv_build`:

| PyPI name               | Import path             | Source directory                           | `module-name`           |
| ----------------------- | ----------------------- | ------------------------------------------ | ----------------------- |
| `swiss-ai-hub-core`     | `swiss_ai_hub.core`     | `packages/core/swiss_ai_hub/core/`         | `swiss_ai_hub.core`     |
| `swiss-ai-hub-agent`    | `swiss_ai_hub.agent`    | `packages/agent/swiss_ai_hub/agent/`       | `swiss_ai_hub.agent`    |
| `swiss-ai-hub-api`      | `swiss_ai_hub.api`      | `packages/api/swiss_ai_hub/api/`           | `swiss_ai_hub.api`      |
| `swiss-ai-hub-bot`      | `swiss_ai_hub.bot`      | `packages/bot/swiss_ai_hub/bot/`           | `swiss_ai_hub.bot`      |
| `swiss-ai-hub-pipeline` | `swiss_ai_hub.pipeline` | `packages/pipeline/swiss_ai_hub/pipeline/` | `swiss_ai_hub.pipeline` |
| `swiss-ai-hub-process`  | `swiss_ai_hub.process`  | `packages/process/swiss_ai_hub/process/`   | `swiss_ai_hub.process`  |

The `uv_build` backend uses `module-root = ""` and `module-name = "swiss_ai_hub.<scope>"` to locate the source code
within each workspace member.

### File and directory naming: snake_case everywhere

All Python source files and directories are renamed from CamelCase to snake_case:

```
# Before
ExpertAskingAgent/
├── ExpertAskingAgent.py
├── ExpertAskingAgentConfig.py
├── events/
│   ├── AnswerStopEvent.py
│   └── AskExpertEvent.py
└── tests/
    └── test_ExpertAskingAgent.py

# After
expert_asking_agent/
├── expert_asking_agent.py
├── expert_asking_agent_config.py
├── events/
│   ├── answer_stop_event.py
│   └── ask_expert_event.py
└── tests/
    └── test_expert_asking_agent.py
```

This resolves the import ambiguity that prevented proper `__init__.py` usage. With CamelCase,
`from agents import ExpertAskingAgent` is ambiguous — it could mean the module `ExpertAskingAgent.py` or the class
`ExpertAskingAgent` from `__init__.py`. With snake_case, `expert_asking_agent` (module) and `ExpertAskingAgent` (class)
are lexically distinct.

### Public interface via `__init__.py`

Each top-level folder within a package now has an `__init__.py` that lazily exports the public interface using
`TYPE_CHECKING` + `__getattr__`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent

__all__ = ["StartEvent"]

_LAZY_IMPORTS: dict[str, str] = {
    "StartEvent": "swiss_ai_hub.core.events.agent.control.start.start_event",
}

def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib
        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
```

Lazy loading is essential because the event system uses `__pydantic_init_subclass__` auto-registration — eager barrel
imports would trigger duplicate registration errors. The `TYPE_CHECKING` block provides static analysis support without
runtime side effects.

Two import rules follow from this:

- **Within a package**: always import via full module path, never through `__init__.py`.\
  `from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent`

- **Across packages**: always import through the target package's `__init__.py`.\
  `from swiss_ai_hub.core.events.agent import StartEvent`

### License change

All packages move from `LicenseRef-Proprietary` to `Apache-2.0`.

## Consequences

### Positive

- CamelCase import ambiguity is eliminated — `__init__.py` public interfaces now work correctly
- Internal file reorganization no longer breaks cross-package consumers
- Namespace packages enable independent installation (`pip install swiss-ai-hub-core`) with a shared import prefix
- Standard `packages/` layout clearly separates source code from docs, infra, and CI
- Consistent `snake_case` aligns with PEP 8 and standard Python tooling expectations
- Clear brand identity for PyPI, npm, and Docker registries

### Trade-offs

- Every import in the codebase changes — large diff with high merge conflict risk for in-flight branches
- Developer muscle memory and existing documentation references become stale simultaneously
- The `TYPE_CHECKING` + `__getattr__` pattern in `__init__.py` adds boilerplate compared to simple re-exports, but is
  necessary to avoid auto-registration side effects in the event system
