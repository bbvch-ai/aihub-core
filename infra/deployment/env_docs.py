"""
Render the environment-variables reference page for the deployment-guide
docs site, grouping every variable by role using :class:`ComposeUsage`.

The page has three sections corresponding to the three :class:`Role` values.
Each renderer takes the per-section list of variable names plus the shared
``ComposeUsage`` and ``ConsumerIndex``, and emits a markdown table.
"""

from pathlib import Path

from env_inventory import (
    ComposeUsage,
    Consumer,
    ConsumerIndex,
    Role,
    analyze_compose,
)


# Maps each env var name to the set of compose-variant labels (e.g. "CPU", "GPU")
# in which the variable appears. Used to tag GPU-only vars in the docs.
type VariantOrigins = dict[str, set[str]]


def write_env_var_docs(
    output_path: Path,
    consumers: ConsumerIndex,
    compose_variants: dict[str, Path],
) -> None:
    """Render the environment-variables reference page for the deployment guide.

    `compose_variants` maps a short label (e.g. "CPU", "GPU") to the rendered
    docker-compose file for that variant. The first variant is treated as the
    base; any subsequent variant is documented as a *pure extension* in its own
    trailing section listing the additional variables it needs.
    """
    if not compose_variants:
        raise ValueError("write_env_var_docs requires at least one compose variant")

    base_label, *extension_labels = compose_variants
    compose = analyze_compose(list(compose_variants.values()))
    origins = _compute_variant_origins(compose_variants)
    by_role = _group_by_role(consumers, compose)

    # Universe = anything we'd render in any role table (Pydantic consumers +
    # compose interpolations + compose-supplied env-block keys). Vars without
    # a compose origin (consumer-only, e.g. optional Azure / SharePoint
    # secrets) belong to the base — operators using only the base must still
    # see them in the docs even though they're never referenced by compose.
    universe = set(consumers) | compose.all_interpolated | compose.supplied_vars
    base_vars = {n for n in universe if base_label in origins.get(n, set())} | (universe - origins.keys())

    lines = list(_render_intro(base_label, extension_labels))
    lines.append(f"## Variables for the base deployment (`{base_label}`)")
    lines.append("")
    _render_role_sections(lines, by_role, consumers, compose, names_filter=base_vars)

    for ext_label in extension_labels:
        ext_vars = {name for name, where in origins.items() if ext_label in where and base_label not in where}
        ext_section: list[str] = []
        _render_role_sections(ext_section, by_role, consumers, compose, names_filter=ext_vars)

        lines.append(f"## Additional variables for `{ext_label}` deployments")
        lines.append("")
        if ext_section:
            lines.append(
                f"These variables are only needed when running the `{ext_label}` variant. "
                f"They extend the base set above; everything in the base section still applies."
            )
            lines.append("")
            lines.extend(ext_section)
        else:
            lines.append(
                f"The `{ext_label}` variant currently does not introduce any operator-controlled "
                f"variables beyond the base set above."
            )
            lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _render_role_sections(
    lines: list[str],
    by_role: dict[Role, list[str]],
    consumers: ConsumerIndex,
    compose: ComposeUsage,
    names_filter: set[str],
) -> None:
    """Append the three role tables, restricted to vars in `names_filter`."""
    compose_required = [n for n in by_role[Role.COMPOSE_REQUIRED] if n in names_filter]
    app_required = [n for n in by_role[Role.APP_REQUIRED] if n in names_filter]
    optional = [n for n in by_role[Role.OPTIONAL] if n in names_filter]

    if compose_required:
        lines.extend(_render_compose_required_section(compose_required, consumers, compose))
    if app_required:
        lines.extend(_render_app_required_section(app_required, consumers, compose))
    if optional:
        lines.extend(_render_optional_section(optional, consumers, compose))


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------


def _group_by_role(consumers: ConsumerIndex, compose: ComposeUsage) -> dict[Role, list[str]]:
    universe = sorted(set(consumers) | compose.all_interpolated)
    by_role: dict[Role, list[str]] = {role: [] for role in Role}
    for name in universe:
        role = compose.role_for(name, consumers.get(name, []))
        if role is not None:
            by_role[role].append(name)
    return by_role


def _compute_variant_origins(compose_variants: dict[str, Path]) -> VariantOrigins:
    """For each env var, which compose variants reference or supply it."""
    origins: dict[str, set[str]] = {}
    for label, path in compose_variants.items():
        usage = analyze_compose([path])
        seen = usage.all_interpolated | usage.supplied_vars
        for name in seen:
            origins.setdefault(name, set()).add(label)
    return origins


# ---------------------------------------------------------------------------
# Section renderers — each yields lines for its part of the page
# ---------------------------------------------------------------------------


def _render_intro(base_label: str, extension_labels: list[str]) -> list[str]:
    lines = [
        "---",
        "title: Environment Variables",
        "description: Reference of every environment variable used by the Swiss AI Hub deployment",
        "---",
        "",
        "# Environment Variables",
        "",
        (
            "This page lists every environment variable read by the Swiss AI Hub deployment, "
            "organized by role. It is auto-generated from the Pydantic settings classes in "
            "`packages/*/swiss_ai_hub/**/*settings.py` and the docker-compose templates. "
            "Do not edit by hand — run `make generate-env-docs` to refresh."
        ),
        "",
        "Variables fall into three roles:",
        "",
        "- **Compose-required** — referenced as `${VAR}` in `docker-compose.yml`. Must be set in `.env` because the project's compose templates do not provide fallback defaults.",
        "- **App-required** — read as a required field by a Pydantic `BaseSettings` class. The application refuses to start if unset.",
        "- **Optional** — has a default in code. Set in `.env` only to override the default.",
        "",
    ]
    if extension_labels:
        lines.append(
            f"The deployment has a base variant (`{base_label}`) plus pure-extension variants "
            f"({', '.join(f'`{v}`' for v in extension_labels)}). The first section below lists "
            f"every variable required by the base; subsequent sections list only the extra "
            f"variables each extension introduces on top of the base."
        )
        lines.append("")
    return lines


def _render_compose_required_section(names: list[str], consumers: ConsumerIndex, compose: ComposeUsage) -> list[str]:
    lines = [
        "### Required by docker-compose interpolation",
        "",
        (
            "These variables are referenced as `${VAR}` (without a `${VAR:-default}` "
            "fallback) somewhere in `docker-compose.yml`. Compose-parse will fail or "
            "render empty values if `.env` does not define them. The Consumer column "
            "shows the Pydantic settings field that reads the variable when our Python "
            "code consumes it; otherwise it points at the config file that embeds it "
            "(Keycloak realm import, identity-provider config, etc.) or — if neither — "
            "is left empty. The Service(s) column lists the compose service(s) whose "
            "`environment:` block receives the variable."
        ),
        "",
        "| Variable | Consumer | Service(s) | Description |",
        "|---|---|---|---|",
    ]
    for name in names:
        cs = consumers.get(name, [])
        lines.append(
            f"| `{name}` | {_consumer_label(name, cs, compose)} | "
            f"{_render_services(name, compose)} | {_render_description(cs)} |"
        )
    lines.append("")
    return lines


def _render_app_required_section(names: list[str], consumers: ConsumerIndex, compose: ComposeUsage) -> list[str]:
    lines = [
        "### Required by SDK settings classes (not used by the default deployment)",
        "",
        (
            "These variables are declared as required fields on a Pydantic `BaseSettings` "
            "class and are **not** consumed by any service in the default docker-compose stack. "
            "The empty Service(s) column reflects this: no container in the default deployment "
            "loads the settings class. They become operationally required only when a custom "
            "agent, pipeline, or other extension is added to docker-compose that activates the "
            "corresponding SDK functionality (e.g. the SharePoint connector or Azure Document "
            "Intelligence loader). Until then, leaving the placeholders unchanged is fine — "
            "Pydantic only validates the class when something instantiates it."
        ),
        "",
        "| Variable | Consumer | Service(s) | Description |",
        "|---|---|---|---|",
    ]
    for name in names:
        cs = consumers[name]
        primary = next(c for c in cs if c.required)
        lines.append(
            f"| `{name}` | `{primary.cls_name}.{primary.field_name}` | "
            f"{_render_services(name, compose)} | {_render_description([primary])} |"
        )
    lines.append("")
    return lines


def _render_optional_section(names: list[str], consumers: ConsumerIndex, compose: ComposeUsage) -> list[str]:
    lines = [
        "### Optional: override platform defaults",
        "",
        (
            "These variables have sensible defaults (or are supplied to containers by "
            "docker-compose) and do not need to be set in `.env`. Add them only to "
            "override the default. Vars marked `(supplied by compose)` are required "
            "by the application but get their value injected through `docker-compose.yml`, "
            "so setting them in `.env` has no effect."
        ),
        "",
        "| Variable | Consumer | Default | Service(s) | Description |",
        "|---|---|---|---|---|",
    ]
    for name in names:
        primary = consumers[name][0]
        lines.append(
            f"| `{name}` | `{primary.cls_name}.{primary.field_name}` "
            f"| {_render_default(name, primary, compose)} | "
            f"{_render_services(name, compose)} | {_render_description([primary])} |"
        )
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Cell renderers
# ---------------------------------------------------------------------------


def _consumer_label(name: str, var_consumers: list[Consumer], compose: ComposeUsage) -> str:
    """Render the Consumer column. Preference order:

    1. Pydantic settings field (our Python code reads it).
    2. Config-template file basename (the var is expanded inside a mounted config).
    3. Empty cell — the Service(s) column already lists the receiving container.
    """
    if var_consumers:
        primary = var_consumers[0]
        return f"`{primary.cls_name}.{primary.field_name}`"
    files = compose.config_template_refs.get(name, [])
    if files:
        return ", ".join(f"`{f}`" for f in files)
    return ""


def _render_services(name: str, compose: ComposeUsage) -> str:
    """Render the Service(s) column — comma-separated compose services that
    receive the var via their ``environment:`` block (literally or via
    ``${VAR}`` interpolation). Empty if no compose service supplies the var."""
    services = compose.supplied_to_services.get(name, [])
    if not services:
        return ""
    return ", ".join(f"`{s}`" for s in services)


def _render_default(name: str, primary: Consumer, compose: ComposeUsage) -> str:
    if primary.default_repr is not None:
        return f"`{primary.default_repr}`"
    if name in compose.supplied_to_services:
        return "_(supplied by compose)_"
    return ""


def _render_description(var_consumers: list[Consumer]) -> str:
    desc = var_consumers[0].description if var_consumers else None
    return _md_escape(desc)


def _md_escape(text: str | None) -> str:
    if not text:
        return ""
    return text.replace("|", "\\|").replace("\n", " ").strip()
