"""
Shared primitives for inspecting environment-variable usage across the platform.

Two consumers build on this module:
- ``env_check.py`` — diffs `.env` against rendered docker-compose files and
  reports the gaps.
- ``env_docs.py``  — emits the auto-generated environment-variables reference
  page for the deployment guide.

The data model has three parts:

1. **Pydantic side** — :func:`build_consumers` walks every BaseSettings class in
   ``packages/*/swiss_ai_hub/**/*settings*.py`` and returns the
   :data:`ConsumerIndex` mapping ``ENV_NAME -> [Consumer, ...]``.

2. **Compose side** — :func:`analyze_compose` parses one or more rendered
   compose files plus the config-file templates and returns a
   :class:`ComposeUsage` describing where every env var is referenced and
   which container ends up receiving it.

3. **Classification** — given a ``ComposeUsage`` and a per-var consumer list,
   :meth:`ComposeUsage.role_for` produces a :class:`Role` (or ``None`` for
   orphans). Roles are the operator-facing taxonomy:

   - ``COMPOSE_REQUIRED``: docker-compose interpolates ``${VAR}`` without a
     fallback. The variable must be defined in ``.env``.
   - ``APP_REQUIRED``: a Pydantic settings field has no default AND compose
     does not supply the variable to any container. The application will fail
     to start unless ``.env`` defines it.
   - ``OPTIONAL``: any other settings consumer (defaults exist, or the var is
     supplied by compose to its container so ``.env`` is not the source).
"""

import importlib.util
import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings
from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings

# ---------------------------------------------------------------------------
# Paths and patterns
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
PACKAGES_DIR = REPO_ROOT / "packages"
CONFIG_TEMPLATES_DIR = Path(__file__).parent.resolve() / "templates" / "configs"

_SETTINGS_GLOBS = ["**/settings.py", "**/*_settings.py"]

# `rclone_source_factory.py` defines `RcloneSourceSettings`, whose env_prefix is
# set DYNAMICALLY at call time (`RcloneSourceSettings.load("AZUREBLOB")` builds
# a per-source subclass with prefix `RCLONE_AZUREBLOB_`). Static introspection
# sees only the parent class — which has no prefix — so its fields would be
# indexed as bare names like `NAME` and `TYPE`. Those don't correspond to real
# env vars and would collide with anything else named that way. Skip the file.
_SKIP_FILES = {"rclone_source_factory.py"}

_ENV_KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=")
# Captures: var name + the operator (`-`, `:-`, `+`, `:+`, `?`, `:?`) if any.
# `${VAR}`            -> compose interpolation without fallback (must be in .env)
# `${VAR:-default}`   -> compose interpolation with default (optional in .env)
_COMPOSE_REF_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(:?[-+?])?[^}]*\}")
# LiteLLM config syntax: `os.environ/VAR_NAME` instructs LiteLLM to resolve the
# value from the process environment at runtime.
_OS_ENVIRON_RE = re.compile(r"os\.environ/([A-Z_][A-Z0-9_]*)")
_CONFIG_REF_PATTERNS = [_COMPOSE_REF_RE, _OS_ENVIRON_RE]

_ENV_VAR_NAME_RE = re.compile(r"[A-Z_][A-Z0-9_]*")


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Role(StrEnum):
    COMPOSE_REQUIRED = "compose-required"
    APP_REQUIRED = "app-required"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class Consumer:
    """One Pydantic settings field that reads an env var at runtime."""

    cls_name: str
    field_name: str
    required: bool
    default_repr: str | None
    description: str | None


# Public alias to make signatures self-documenting.
type ConsumerIndex = dict[str, list[Consumer]]
type FilesByVar = dict[str, list[str]]


@dataclass(frozen=True)
class ComposeUsage:
    """Everything env-related extracted from a set of rendered compose files
    plus the config-file templates that accompany them.

    Use :func:`analyze_compose` to construct.
    """

    interp_required: set[str] = field(default_factory=set)
    interp_with_default: set[str] = field(default_factory=set)
    supplied_to_services: FilesByVar = field(default_factory=dict)
    config_template_refs: FilesByVar = field(default_factory=dict)

    @property
    def all_interpolated(self) -> set[str]:
        return self.interp_required | self.interp_with_default

    @property
    def supplied_vars(self) -> set[str]:
        return set(self.supplied_to_services)

    def role_for(self, var: str, var_consumers: list[Consumer]) -> Role | None:
        """Classify a single var into one of three roles, or ``None`` if irrelevant."""
        if var in self.interp_required:
            return Role.COMPOSE_REQUIRED
        is_supplied = var in self.supplied_to_services
        if any(c.required for c in var_consumers) and not is_supplied:
            return Role.APP_REQUIRED
        if var_consumers:
            return Role.OPTIONAL
        return None


# ---------------------------------------------------------------------------
# Pydantic settings discovery
# ---------------------------------------------------------------------------


def build_consumers() -> ConsumerIndex:
    """Walk every BaseSettings class in `packages/` and return ENV_NAME -> Consumers."""
    consumers: ConsumerIndex = defaultdict(list)
    for index, path in enumerate(_discover_settings_files()):
        module = _import_module_safely(path, index)
        if module is None:
            continue
        for cls in _settings_classes_in(module):
            prefix = cls.model_config.get("env_prefix", "") if hasattr(cls, "model_config") else ""
            for field_name, info in cls.model_fields.items():
                env_name = f"{prefix}{field_name}".upper()
                consumers[env_name].append(
                    Consumer(
                        cls_name=cls.__name__,
                        field_name=field_name,
                        required=info.is_required(),
                        default_repr=None if info.is_required() else repr(info.default),
                        description=info.description,
                    )
                )
    return dict(consumers)


def _discover_settings_files() -> list[Path]:
    found: set[Path] = set()
    for pkg_dir in PACKAGES_DIR.iterdir():
        src_root = pkg_dir / "swiss_ai_hub"
        if not src_root.is_dir():
            continue
        for pattern in _SETTINGS_GLOBS:
            for path in src_root.glob(pattern):
                if path.name in _SKIP_FILES:
                    continue
                if "__pycache__" in path.parts or any(p in {"test", "tests", "testing"} for p in path.parts):
                    continue
                found.add(path)
    return sorted(found)


def _import_module_safely(path: Path, index: int):
    """Import a settings file under a synthetic name; return None on failure."""
    spec = importlib.util.spec_from_file_location(f"_aihub_envcheck_{index}", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        print(f"  warn: skipped {path.relative_to(REPO_ROOT)}: {type(exc).__name__}: {exc}")
        return None
    return module


def _settings_classes_in(module) -> list[type[BaseSettings]]:
    out: list[type[BaseSettings]] = []
    module_name = getattr(module, "__name__", None)
    for attr in vars(module).values():
        if not isinstance(attr, type):
            continue
        if not issubclass(attr, BaseSettings) or attr is BaseSettings:
            continue
        if attr.__module__ != module_name:
            continue
        # Identity comparison — robust against an unrelated class that
        # happens to be named "EnvironmentSettings" elsewhere in the codebase.
        if attr is EnvironmentSettings:
            continue
        if not attr.model_fields:
            continue
        out.append(attr)
    return out


# ---------------------------------------------------------------------------
# Env-file parsing
# ---------------------------------------------------------------------------


def read_env_keys(path: Path) -> set[str]:
    """Variable names defined in an env file (skipping comments and blanks)."""
    keys: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _ENV_KEY_RE.match(line)
        if match:
            keys.add(match.group(1))
    return keys


# ---------------------------------------------------------------------------
# Compose-file parsing
# ---------------------------------------------------------------------------


def analyze_compose(compose_files: list[Path]) -> ComposeUsage:
    """Build a :class:`ComposeUsage` from the union of one or more compose files.

    Pass a single CPU compose for `--check-env`, both CPU+GPU compose files for
    the doc generator (so the docs cover variables introduced in either variant).
    Always also scans the config-file templates next to this module.
    """
    interp_required: set[str] = set()
    interp_with_default: set[str] = set()
    supplied_to_services: dict[str, set[str]] = defaultdict(set)

    for path in compose_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in _COMPOSE_REF_RE.finditer(text):
            name, fallback_op = match.group(1), match.group(2)
            (interp_with_default if fallback_op else interp_required).add(name)
        for var, services in _read_compose_supplied_by_service(path).items():
            supplied_to_services[var] |= services

    return ComposeUsage(
        interp_required=interp_required,
        interp_with_default=interp_with_default,
        supplied_to_services={var: sorted(svcs) for var, svcs in supplied_to_services.items()},
        config_template_refs=_collect_config_template_refs(),
    )


def _read_compose_supplied_by_service(path: Path) -> dict[str, set[str]]:
    """Map env var name -> services that receive it via any service field.

    A service is recorded for a var if either:
    - the var name appears as a key in the service's `environment:` block (so
      its value reaches the container under that exact name), OR
    - the var appears as `${VAR}` *anywhere* in the service mapping —
      ``environment:``, ``labels:``, ``command:``, ``entrypoint:``,
      ``volumes:``, ``ports:``, etc. Examples:
        - ``KC_BOOTSTRAP_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}`` records
          ``keycloak`` as a consumer of ``KEYCLOAK_ADMIN_PASSWORD``.
        - ``- "traefik.http.middlewares.admin.basicauth.users=admin:${ADMIN_PASSWORD_HASH}"``
          records the labelled service as a consumer of ``ADMIN_PASSWORD_HASH``.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    by_var: dict[str, set[str]] = defaultdict(set)
    for service_name, service in (data.get("services") or {}).items():
        # Special-case the environment: block so we record the LHS keys (which
        # are env-var names received by the container even when the value is a
        # literal). Every other service field only contributes via ${VAR}
        # interpolation, captured by the recursive walk below.
        for key, _value in _iter_environment_entries(service.get("environment")):
            if _ENV_VAR_NAME_RE.fullmatch(key):
                by_var[key].add(service_name)
        for var in _iter_compose_refs_in(service):
            by_var[var].add(service_name)
    return by_var


def _iter_environment_entries(env) -> Iterator[tuple[str, str]]:
    """Yield (key, value) for each entry in a docker-compose environment block."""
    if isinstance(env, dict):
        for k, v in env.items():
            yield str(k), "" if v is None else str(v)
    elif isinstance(env, list):
        for entry in env:
            if isinstance(entry, str) and "=" in entry:
                k, v = entry.split("=", 1)
                yield k, v


def _iter_compose_refs_in(node) -> Iterator[str]:
    """Recursively yield every ``${VAR}`` name found in any string anywhere in
    a parsed docker-compose mapping. Walks dicts, lists, and scalar leaves.
    Catches refs in `labels:`, `command:`, `entrypoint:`, `volumes:`, etc.
    """
    if isinstance(node, str):
        for match in _COMPOSE_REF_RE.finditer(node):
            yield match.group(1)
    elif isinstance(node, dict):
        for value in node.values():
            yield from _iter_compose_refs_in(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_compose_refs_in(item)


def _collect_config_template_refs() -> FilesByVar:
    """Map env var name -> sorted list of config-template basenames that reference it.

    Scans `infra/deployment/templates/configs/*.j2` for both `${VAR}` and the
    LiteLLM-specific `os.environ/VAR` syntax. These are the env vars that get
    expanded inside a config file mounted into a container at runtime — useful
    for attributing variables that aren't passed via compose's `environment:`
    block but reach the container through a mounted config (Keycloak realm
    import, identity-provider config, LiteLLM config, etc.).
    """
    refs: dict[str, set[str]] = defaultdict(set)
    for path in sorted(CONFIG_TEMPLATES_DIR.glob("*.j2")):
        text = path.read_text(encoding="utf-8")
        for pattern in _CONFIG_REF_PATTERNS:
            for match in pattern.finditer(text):
                refs[match.group(1)].add(path.name.removesuffix(".j2"))
    return {var: sorted(files) for var, files in refs.items()}


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def format_repo_path(path: Path) -> str:
    """Render a path relative to the repo root for human-readable logging."""
    return str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
