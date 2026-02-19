# Migrate from Poetry to uv for Package Management

## Context

AI-Hub is a Python monorepo with six packages (`aihub_lib`, `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`,
`aihub_process`) that share a common library (`aihub_lib`). Previously, each package used Poetry as its package manager
with independent `pyproject.toml` and `poetry.lock` files.

Poetry does not natively support monorepo workspaces. To work around this, the project maintained a custom
`switch_dependencies.py` script that toggled inter-package dependencies between local path references (for development)
and Git URL references (for CI/CD and production). This created fragile tooling, required manual intervention when
switching contexts, and caused confusion for new contributors. Each package had its own virtual environment and lock
file, resulting in seven separate dependency resolution steps during CI and slow Docker builds.

## Decision Drivers

- **Native workspace support**\
  uv provides first-class monorepo workspaces with a single `uv.lock` at the root and automatic resolution of
  inter-package dependencies via `[tool.uv.sources]` with `{ workspace = true }`. This eliminates the need for
  `switch_dependencies.py` entirely.
- **Single virtual environment and lock file**\
  All six packages share one `.venv` and one `uv.lock`, ensuring consistent dependency versions across the entire
  monorepo. Poetry required seven separate lock files and virtual environments.
- **10-100x faster dependency resolution**\
  uv resolves and installs dependencies significantly faster than Poetry. `uv sync --all-packages` completes in seconds
  where `poetry install` across all packages took minutes.
- **Simplified Docker builds**\
  Docker images use `uv sync --locked --no-dev --package <name>` to install only production dependencies for a specific
  package. No Poetry installation is needed in the runtime stage — the `.venv/bin` directory is added to PATH directly.
- **PEP 621 compliance**\
  uv uses the standard `[project]` table in `pyproject.toml` (PEP 621) instead of Poetry's non-standard
  `[tool.poetry]` section. This improves compatibility with other Python tooling.
- **Active development and community momentum**\
  uv is under active development by Astral (the team behind Ruff) with rapid feature additions and strong community
  adoption.

## Decision

We migrate all packages, CI/CD pipelines, Dockerfiles, and documentation from Poetry to uv:

**Package configuration**: All `pyproject.toml` files use the standard `[project]` table with `uv_build` as the build
backend. Inter-package dependencies are declared in `[tool.uv.sources]` at the workspace root and inherited by all
members.

**Development workflow**: `uv sync --all-packages` from the workspace root installs all packages into a single shared
virtual environment. `uv run` replaces `poetry run` in all Makefiles and documentation.

**CI/CD**: GitHub Actions use `astral-sh/setup-uv@v7` with caching enabled. A single `uv sync --all-packages --dev`
step replaces per-package Poetry installs.

**Docker**: Multi-stage builds copy uv from `ghcr.io/astral-sh/uv:latest` and use
`uv sync --locked --no-dev --package <name>` for production installs. Runtime stages reference `.venv/bin` directly
without needing uv or Poetry installed.

**Documentation**: All developer guides, SDK documentation, and command references are updated to reflect uv commands.

## Consequences

### Positive

- Eliminated `switch_dependencies.py` and the `use-local-core`/`use-remote-core` workflow
- Single `uv.lock` and `.venv` simplify dependency management and reduce confusion
- CI/CD pipeline is faster and simpler (one install step instead of seven)
- Docker builds are faster and produce smaller images (no Poetry in runtime stage)
- Standard PEP 621 metadata improves interoperability with Python ecosystem tools
- New contributor onboarding is simpler: `uv sync --all-packages` sets up everything

### Trade-offs

- Team must learn uv commands (minimal learning curve — commands are similar to Poetry)
- SDK documentation changes affect external customers who followed Poetry-based setup guides
- uv is newer than Poetry and may have less community knowledge available for troubleshooting
