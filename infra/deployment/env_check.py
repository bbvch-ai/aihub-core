"""
Diff a `.env` file against a rendered docker-compose file.

For every variable in the union of (env-defined, compose-interpolated,
Pydantic-consumed) we ask three questions:

  1. Is the variable defined in the env file?
  2. What role has the deployment assigned to it (compose-required / app-required /
     optional / orphan)?
  3. Is the combination consistent?

Inconsistent combinations (orphaned env entries, compose-required vars missing
from `.env`, app-required vars missing from `.env` and not supplied by compose)
become ERRORs. Optional vars that the operator chose to override become INFOs.
Strict mode raises ``SystemExit`` if any ERROR is reported.
"""

from dataclasses import dataclass
from pathlib import Path

from env_inventory import (
    ComposeUsage,
    Consumer,
    ConsumerIndex,
    Role,
    analyze_compose,
    format_repo_path,
    read_env_keys,
)


@dataclass(frozen=True)
class _Finding:
    severity: str  # "ERROR" | "INFO"
    message: str


def check_env_vs_compose(
    env_file: Path,
    compose_file: Path,
    consumers: ConsumerIndex,
    label: str,
    strict: bool,
) -> bool:
    """Diff env file vs compose file. Returns True if no ERRORs were reported."""
    defined = read_env_keys(env_file)
    compose = analyze_compose([compose_file])

    findings: list[_Finding] = []
    universe = defined | compose.all_interpolated | set(consumers)
    for name in sorted(universe):
        var_consumers = consumers.get(name, [])
        finding = _classify_var(name, defined, compose.role_for(name, var_consumers), var_consumers)
        if finding is not None:
            findings.append(finding)

    _print_summary(label, env_file, compose_file, defined, compose, consumers)
    _print_findings(findings)

    has_errors = any(f.severity == "ERROR" for f in findings)
    if strict and has_errors:
        raise SystemExit(f"{label}: env/compose mismatch (strict mode)")
    return not has_errors


def _classify_var(
    name: str,
    defined: set[str],
    role: Role | None,
    var_consumers: list[Consumer],
) -> _Finding | None:
    """Produce a finding for a single var if its env/role combination is notable."""
    in_env = name in defined

    if in_env and role is None:
        return _Finding(
            "ERROR",
            f"{name:45s} defined in .env but unused by compose AND no settings class consumes it — safe to remove",
        )

    if not in_env and role is Role.COMPOSE_REQUIRED:
        desc_suffix = _describe(var_consumers[0].description if var_consumers else None)
        return _Finding(
            "ERROR",
            f"{name:45s} required by docker-compose interpolation — add to .env{desc_suffix}",
        )

    if not in_env and role is Role.APP_REQUIRED:
        first_required = next(c for c in var_consumers if c.required)
        return _Finding(
            "ERROR",
            f"{name:45s} required by {first_required.cls_name}.{first_required.field_name}"
            f" — add to .env{_describe(first_required.description)}",
        )

    if in_env and role is Role.OPTIONAL:
        defaults = ", ".join(sorted({f"{c.cls_name}={c.default_repr}" for c in var_consumers}))
        return _Finding("INFO", f"{name:45s} override active (defaults: {defaults})")

    return None


def _describe(description: str | None) -> str:
    return f" ({description})" if description else ""


def _print_summary(
    label: str,
    env_file: Path,
    compose_file: Path,
    defined: set[str],
    compose: ComposeUsage,
    consumers: ConsumerIndex,
) -> None:
    print(f"\n  Env consistency check ({label})")
    print(f"    env file:  {format_repo_path(env_file)}")
    print(f"    compose:   {format_repo_path(compose_file)}")
    print(f"    {len(defined)} variables defined in the env file")
    print(f"    {len(compose.interp_required)} variables docker-compose interpolates from .env (must be set)")
    print(f"    {len(compose.interp_with_default)} variables docker-compose interpolates with a fallback (optional)")
    print(f"    {len(compose.supplied_to_services)} variables docker-compose injects into containers via environment blocks")
    print(f"    {len(consumers)} variables Pydantic settings classes read at runtime")


def _print_findings(findings: list[_Finding]) -> None:
    by_severity: dict[str, list[_Finding]] = {"ERROR": [], "INFO": []}
    for f in findings:
        by_severity[f.severity].append(f)
    for severity in ("ERROR", "INFO"):
        items = by_severity[severity]
        if items:
            print(f"    {severity} ({len(items)}):")
            for f in items:
                print(f"      - {f.message}")
    if not findings:
        print("    OK: env, compose, and settings agree")
