"""
Generates Docker Compose and service configuration files from Jinja2 templates.
Based on a matrix of stages (dev/local/nightly/latest) and hardware (CPU/GPU).

Supports a --release mode to generate self-contained deployment bundles with
version-pinned image tags and clean filenames (no stage/hardware suffixes).
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

# Note: env_check / env_docs / env_inventory are imported lazily inside the
# CLI branches that need them. They depend on pydantic_settings, which is only
# installed when `uv sync --all-packages` has run. CI workflows that only do
# `make generate-compose` (e.g. test-backup-e2e.yml) skip the all-packages sync,
# so these imports must not fire at module load time.

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
ROOT_DIR = Path(__file__).parent.parent.resolve()
DEPLOYMENT_DIR = Path(__file__).parent.resolve()

# Stages and hardware variants
STAGES = ["dev", "local", "latest", "nightly", "build"]
GPU_MODES = {False: "", True: ".gpu"}

# Configuration specs: (template_path, output_dir, output_name_pattern)
CONFIG_SPECS = [
    # Docker Compose - always required
    ("templates/docker-compose.yml.j2", ROOT_DIR, "docker-compose.{stage}{hardware}.yml"),
    # Keycloak bootstrap configs (realm settings, user profile, startup tenant
    # group, superuser, identity providers) are first-start-only seeds. They are
    # NOT rendered standalone here — they are emitted solely through the merged
    # aihub-realm file consumed by --import-realm (see generate_keycloak_realm /
    # KEYCLOAK_BOOTSTRAP_TEMPLATES). Bootstrap changes stay reviewable via the
    # diff of the merged aihub-realm.{stage}.json output.
    # Keycloak managed configs - reconciled on every start by keycloak-config-cli.
    ("templates/configs/keycloak/managed/10-roles.json.j2", "configs/keycloak/managed", "10-roles.{stage}{hardware}.json"),
    (
        "templates/configs/keycloak/managed/20-client-scopes.json.j2",
        "configs/keycloak/managed",
        "20-client-scopes.{stage}{hardware}.json",
    ),
    (
        "templates/configs/keycloak/managed/30-clients.json.j2",
        "configs/keycloak/managed",
        "30-clients.{stage}{hardware}.json",
    ),
    (
        "templates/configs/keycloak/managed/40-auth-flows.json.j2",
        "configs/keycloak/managed",
        "40-auth-flows.{stage}{hardware}.json",
    ),
    (
        "templates/configs/keycloak/managed/60-service-accounts.json.j2",
        "configs/keycloak/managed",
        "60-service-accounts.{stage}{hardware}.json",
    ),
    # Service configs - optional, skipped if template missing
    ("templates/configs/litellm-config.yml.j2", "configs/litellm", "litellm-config.{stage}{hardware}.yml"),
    ("templates/configs/milvus-config.yml.j2", "configs/milvus", "milvus-config.{stage}{hardware}.yml"),
    ("templates/configs/nats-config.conf.j2", "configs/nats", "nats-config.{stage}{hardware}.conf"),
    ("templates/configs/dagster-config.yml.j2", "configs/dagster", "dagster-config.{stage}{hardware}.yml"),
    ("templates/configs/workspace.yml.j2", "configs/dagster", "workspace.{stage}{hardware}.yml"),
    ("templates/configs/backup-dagster.yml.j2", "configs/backup", "backup-dagster.{stage}{hardware}.yml"),
    ("templates/configs/backup-workspace.yml.j2", "configs/backup", "backup-workspace.{stage}{hardware}.yml"),
    ("templates/configs/otel-config.yml.j2", "configs/otel", "otel-config.{stage}{hardware}.yml"),
    ("templates/configs/traefik-config.yml.j2", "configs/traefik", "traefik-config.{stage}{hardware}.yml"),
    ("templates/configs/traefik-middlewares.yml.j2", "configs/traefik", "middlewares.{stage}{hardware}.yml"),
    ("templates/configs/traefik-tls.yml.j2", "configs/traefik", "tls.{stage}{hardware}.yml"),
    # Static scripts - no stage/hardware variations
    ("templates/configs/clickhouse-backup.xml.j2", "configs/clickhouse", "clickhouse-backup.xml"),
    ("templates/configs/init.Dockerfile.j2", "configs/etcd", "init.Dockerfile"),
    ("templates/configs/s3-entrypoint.sh.j2", "configs/seaweedfs", "s3-entrypoint.sh"),
    ("templates/configs/s3-init-buckets.sh.j2", "configs/seaweedfs", "init-buckets.sh"),
    ("templates/configs/pg-init-multiple-dbs.sh.j2", "configs/postgres", "init-multiple-dbs.sh"),
    ("templates/configs/openwebui-init-openwebui.sh.j2", "configs/openwebui", "init-openwebui.sh"),
    ("templates/configs/init_etcd.sh.j2", "configs/etcd", "init_etcd.sh"),
    ("templates/configs/keycloak-entrypoint.sh.j2", "configs/keycloak", "keycloak-entrypoint.sh"),
    # Keycloak theme - static files (no stage/hardware variations)
    ("templates/configs/keycloak-theme-properties.j2", "configs/keycloak/themes/aihub/login", "theme.properties"),
    ("templates/configs/keycloak-theme-login.css.j2", "configs/keycloak/themes/aihub/login/resources/css", "login.css"),
]

# Keycloak realm documents merged into the single aihub-realm file consumed by
# --import-realm on first start. Bootstrap documents are first-start-only seeds
# (realm settings, user profile, groups, superuser, identity providers);
# managed documents are also reconciled on every start by keycloak-config-cli,
# but must appear in the merged file too so fresh boots come up complete without
# waiting for the reconciler (kcc adopts the pre-created entities into its
# remote state).
KEYCLOAK_BOOTSTRAP_TEMPLATES = [
    "templates/configs/keycloak/bootstrap/realm-settings.json.j2",
    "templates/configs/keycloak/bootstrap/components.json.j2",
    "templates/configs/keycloak/bootstrap/groups.json.j2",
    "templates/configs/keycloak/bootstrap/users-superuser.json.j2",
    "templates/configs/keycloak/bootstrap/identity-providers.json.j2",
]
KEYCLOAK_MANAGED_TEMPLATES = [
    "templates/configs/keycloak/managed/10-roles.json.j2",
    "templates/configs/keycloak/managed/20-client-scopes.json.j2",
    "templates/configs/keycloak/managed/30-clients.json.j2",
    "templates/configs/keycloak/managed/40-auth-flows.json.j2",
    "templates/configs/keycloak/managed/60-service-accounts.json.j2",
]

# Static directories copied verbatim (no Jinja2 rendering).
# (source_dir relative to DEPLOYMENT_DIR, output_dir relative to ROOT_DIR)
STATIC_COPY_DIRS = [
    ("templates/openwebui_functions", "configs/openwebui/functions"),
    ("templates/litellm_functions", "configs/litellm"),
]

# Static files copied verbatim (no Jinja2 rendering).
# (source relative to DEPLOYMENT_DIR, output_dir relative to ROOT_DIR, output_name)
STATIC_COPY_FILES = [
    ("templates/configs/keycloak-theme-logo.png", "configs/keycloak/themes/aihub/login/resources/img", "logo.png"),
]

# Additional static files included only in release bundles (non-config files).
# Config files are copied automatically from ROOT_DIR/configs/.
# (source relative to REPO_ROOT, destination relative to variant_dir)
RELEASE_STATIC_FILES = [
    (".env.prod", ".env.template"),
    ("setup-env.sh", "setup-env.sh"),
]


def load_config():
    """Load compose-config.yml"""
    config_path = DEPLOYMENT_DIR / "compose-config.yml"
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Licenses for the images we publish ourselves. The repo's open-source split lives in
# LICENSES.md — this dict mirrors the per-package license assignment so the rendered
# compose files can carry an inline `# License:` comment per service. Keys are the
# compose service-name prefix (= the published image name). Generic placeholders in
# `licenses.config.json#own_images` (e.g. "agent", "process", "pipeline") that have no
# corresponding compose service are omitted.
OWN_IMAGE_LICENSES = {
    "api": "Apache-2.0",
    "bot": "Apache-2.0",
    "web": "AGPL-3.0-or-later",
    "backup": "AGPL-3.0-or-later",
    "sysadmin-api": "AGPL-3.0-or-later",
    "sysadmin-web": "AGPL-3.0-or-later",
    "imap_agent": "Apache-2.0",
    "email_classification_agent": "Apache-2.0",
    "llm_wrapping_agent": "Apache-2.0",
    "few_shot_agent": "Apache-2.0",
    "rag_agent": "Apache-2.0",
    "expert_rag_agent": "Apache-2.0",
    "expert_asking_agent": "Apache-2.0",
    "namespace_selection_agent": "Apache-2.0",
    "memory_writer_agent": "Apache-2.0",
    "retrieval_agent": "Apache-2.0",
    "default_rag_pipeline": "Apache-2.0",
    "shared_rag_pipeline": "Apache-2.0",
    "document_ingestion_pipeline": "Apache-2.0",
    # Backup plane variants (dagster webserver/daemon are wired below; the
    # `backup-code` gRPC server runs our packages/backup code directly).
    "backup-code": "AGPL-3.0-or-later",
    # MinerU upstream is Apache-2.0 with an additional commercial-use threshold
    # clause (see LICENSES.md). We ship thin wrapper images that inherit the
    # upstream terms — the SPDX-identifiable base is Apache-2.0.
    "mineru-api": "Apache-2.0",
    "mineru-vlm": "Apache-2.0",
}

# Aliases that map a compose service-name to the canonical entry name in
# `licenses.config.json#docker_licenses`. Needed because compose uses verbose service
# names like `seaweedfs-master` / `oauth2proxy-attu` while the license matrix groups
# them under `seaweedfs` / `oauth2-proxy`.
DOCKER_LICENSE_ALIASES = {
    "vllm": "vllm-openai",
    "vllm-bge-m3": "vllm-openai",
    "vllm-bge-reranker": "vllm-openai",
    "oauth2proxy-seaweed": "oauth2-proxy",
    "oauth2proxy-attu": "oauth2-proxy",
    "oauth2proxy-backup": "oauth2-proxy",
    "oauth2proxy-dagster": "oauth2-proxy",
    "backup-webserver": "dagster",
    "backup-daemon": "dagster",
    "otel-collector": "opentelemetry-collector-contrib",
    "openwebui-init": "postgres",
    "keycloak-config": "keycloak-config-cli",
}


def _load_license_config():
    """Read licenses.config.json from the repo root (single source of truth for the
    image-license matrix consumed by both generate-license.sh and this script)."""
    path = REPO_ROOT / "licenses.config.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _make_service_license_fn(license_config):
    """Return a Jinja-callable that emits a one-line YAML comment describing the
    license of the named compose service. Three lookup tiers:
      1. OWN_IMAGE_LICENSES (with hyphen/underscore variants)
      2. docker_licenses entry — exact, alias, or prefix match
      3. UNKNOWN — surfaces in the generated compose so missing entries are visible
    """
    external = {entry["service"]: entry for entry in license_config.get("docker_licenses", [])}

    def _comment(text: str) -> str:
        # No leading whitespace — the template's `  {{ service_license(...) }}`
        # call already provides the 2-space indent that aligns with the service
        # block below.
        return f"# License: {text}"

    def get(service_name: str) -> str:
        for candidate in (service_name, service_name.replace("-", "_"), service_name.replace("_", "-")):
            if candidate in OWN_IMAGE_LICENSES:
                return _comment(f"{OWN_IMAGE_LICENSES[candidate]} — own image (see LICENSES.md)")
        canonical = DOCKER_LICENSE_ALIASES.get(service_name, service_name)
        if canonical in external:
            return _comment(f"{external[canonical]['license']} — third-party (see LICENSE_REPORT.md)")
        for ext_name in external:
            if service_name.startswith(ext_name + "-") or service_name == ext_name + "-init":
                return _comment(f"{external[ext_name]['license']} — third-party (see LICENSE_REPORT.md)")
        return _comment(f"UNKNOWN — add '{service_name}' to licenses.config.json")

    return get


def load_template(env, template_path):
    """Load a Jinja2 template, return None if not found"""
    return env.get_template(template_path)


def generate_config(template, context, output_path):
    """Render template and write to file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = template.render(context)
    output_path.write_text(rendered, encoding="utf-8")


def generate_keycloak_realm(env, context, output_path):
    """Merge the bootstrap + managed Keycloak documents into the single realm file
    consumed by --import-realm on first start. Duplicate top-level keys must either
    carry identical values (e.g. "realm") or both be lists, which are concatenated
    (e.g. "users" from the superuser seed and the managed service accounts)."""
    merged = {}
    for template_path in KEYCLOAK_BOOTSTRAP_TEMPLATES + KEYCLOAK_MANAGED_TEMPLATES:
        document = json.loads(env.get_template(template_path).render(context))
        for key, value in document.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = merged[key] + value
            elif merged[key] != value:
                raise ValueError(f"Conflicting values for realm key '{key}' in {template_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")


def _strip_stage_hardware(name_pattern):
    """Remove {stage}, {hardware}, and surrounding dots to produce clean filenames.

    Examples:
        'docker-compose.{stage}{hardware}.yml' -> 'docker-compose.yml'
        'litellm-config.{stage}{hardware}.yml' -> 'litellm-config.yml'
        'nats-config.{stage}{hardware}.conf'   -> 'nats-config.conf'
    """
    clean = name_pattern.replace("{hardware}", "").replace("{stage}", "")
    while ".." in clean:
        clean = clean.replace("..", ".")
    return clean


def _pin_image_tags_to_version(config_data, version):
    """Override 'latest' entries in custom service image_tags with version-pinned tags.

    We use stage='latest' for template rendering so all production conditionals
    (GPU services, TLS, auth) work correctly. This function replaces the 'latest'
    image tag with the release version so the rendered compose files reference
    the correct versioned images.

    Only pins services whose 'latest' value follows the per-release publishing
    convention `{service}:latest`. Project-managed images that are published
    out-of-band (e.g. postgres -> pgvector-repack:pg17, playwright ->
    playwright:v1.58.0-jammy) keep their literal pinned tag.
    """
    image_tags = config_data.get("image_tags", {})
    for service, tag_value in image_tags.items():
        if not isinstance(tag_value, dict):
            continue
        if "build" not in tag_value:
            continue
        if tag_value.get("latest") == f"{service}:latest":
            tag_value["latest"] = f"{service}:{version}"


def generate_default(env, config_data):
    """Standard generation: all stages x hardware combinations."""
    stats = {}

    for template_path, output_dir, name_pattern in CONFIG_SPECS:
        template = load_template(env, template_path)

        if not template:
            print(f"Skipping {template_path} (not found)")
            continue

        config_name = template_path.split("/")[-1].replace(".j2", "").replace("-config", "")
        stats[config_name] = 0

        print(f"Loaded template: {template_path}")

        out_dir = ROOT_DIR / output_dir if isinstance(output_dir, str) else output_dir
        needs_stage_hardware = "{stage}" in name_pattern or "{hardware}" in name_pattern

        if needs_stage_hardware:
            for gpu_enabled, hardware in GPU_MODES.items():
                for stage in STAGES:
                    context = {"stage": stage, "gpu_enabled": gpu_enabled, **config_data}
                    filename = name_pattern.format(hardware=hardware, stage=stage)
                    output_path = out_dir / filename

                    generate_config(template, context, output_path)
                    stats[config_name] += 1
        else:
            context = {"stage": "default", "gpu_enabled": False, **config_data}
            output_path = out_dir / name_pattern

            generate_config(template, context, output_path)
            stats[config_name] += 1

    stats["keycloak-realm"] = 0
    for gpu_enabled, hardware in GPU_MODES.items():
        for stage in STAGES:
            context = {"stage": stage, "gpu_enabled": gpu_enabled, **config_data}
            output_path = ROOT_DIR / "configs/keycloak" / f"aihub-realm.{stage}{hardware}.json"
            generate_keycloak_realm(env, context, output_path)
            stats["keycloak-realm"] += 1

    stats["static-copies"] = 0
    for src_rel, dst_rel in STATIC_COPY_DIRS:
        src_dir = DEPLOYMENT_DIR / src_rel
        dst_dir = ROOT_DIR / dst_rel
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in src_dir.iterdir():
            if f.is_file() and not f.name.startswith("test_"):
                shutil.copy2(f, dst_dir / f.name)
                stats["static-copies"] += 1

    for src_rel, dst_rel, filename in STATIC_COPY_FILES:
        src = DEPLOYMENT_DIR / src_rel
        dst = ROOT_DIR / dst_rel / filename
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        stats["static-copies"] += 1

    return stats


def _release_compose_header(project, version, gpu_enabled):
    """Build the header comment block for release compose files."""
    variant = "GPU-enabled" if gpu_enabled else "CPU-only"
    return (
        f"# {project} {version} - Docker Compose Configuration ({variant})\n"
        "#\n"
        f"# This is the {'GPU-enabled' if gpu_enabled else 'CPU-only (no GPU)'} deployment configuration.\n"
        + (
            "# It includes GPU-accelerated services such as vLLM and Speaches.\n"
            if gpu_enabled
            else "# GPU-accelerated services are excluded from this configuration.\n"
        )
        + f"# For the {'CPU-only' if gpu_enabled else 'GPU-enabled'} variant, "
        f"see the {project}-{version}{'' if gpu_enabled else '-gpu'} bundle.\n\n"
    )


def _is_stage_variant(filename):
    """Check if a filename contains a stage-variant suffix (e.g. '.dev.', '.nightly.gpu.')."""
    return any(f".{stage}." in filename or filename.endswith(f".{stage}") for stage in STAGES)


def _copy_release_static_files(variant_dir):
    """Copy static files into a release bundle.

    Copies all non-stage-variant files from ROOT_DIR/configs/ that weren't
    already generated by templates, plus any RELEASE_STATIC_FILES.
    """
    copied = 0

    # Copy non-stage-variant config files from the repo's configs/ directory
    configs_dir = ROOT_DIR / "configs"
    for f in configs_dir.rglob("*"):
        if not f.is_file():
            continue
        if _is_stage_variant(f.name):
            continue
        rel = f.relative_to(configs_dir)
        dst = variant_dir / "configs" / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        copied += 1

    # Copy non-config release files (.env.template, setup-env.sh)
    for src_rel, dst_rel in RELEASE_STATIC_FILES:
        src = REPO_ROOT / src_rel
        if not src.exists():
            continue
        dst = variant_dir / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    return copied


def generate_release(env, config_data, version, output_dir, project):
    """Generate self-contained release bundles for CPU and GPU variants.

    Uses stage='latest' for template rendering so all production conditionals
    (GPU services, TLS, auth, production batch sizes) work correctly. Image tags
    are overridden with version-pinned values, and config_file_suffix='' produces
    clean filenames without stage/hardware suffixes.

    Output folders: <project>-<version> (CPU) and <project>-<version>-gpu (GPU).

    Note: env/compose consistency is verified separately via `make check-env`,
    which diffs `.env.prod` against the same `latest`-stage compose files this
    function would produce. There is no point re-running the same check here
    after the bundle is already on disk — it can't undo the writes, and the
    strict-mode caller path is always coupled to the dedicated `--check-env`
    invocation.
    """
    _pin_image_tags_to_version(config_data, version)
    stats = {}

    variants = [
        (False, f"{project}-{version}"),
        (True, f"{project}-{version}-gpu"),
    ]

    for gpu_enabled, folder_name in variants:
        variant_dir = output_dir / folder_name
        variant_label = "GPU" if gpu_enabled else "CPU"
        print(f"\n  Generating {variant_label} variant -> {variant_dir}")

        for template_path, rel_output_dir, name_pattern in CONFIG_SPECS:
            template = load_template(env, template_path)
            if not template:
                continue

            config_name = template_path.split("/")[-1].replace(".j2", "").replace("-config", "")
            stats.setdefault(config_name, 0)

            needs_stage_hardware = "{stage}" in name_pattern or "{hardware}" in name_pattern

            if needs_stage_hardware:
                context = {
                    "stage": "latest",
                    "gpu_enabled": gpu_enabled,
                    "config_file_suffix": "",
                    **config_data,
                }
                # Inject release header for docker-compose template only
                if "docker-compose" in template_path:
                    context["release_header"] = _release_compose_header(project, version, gpu_enabled)
                filename = _strip_stage_hardware(name_pattern)
            else:
                context = {"stage": "default", "gpu_enabled": False, **config_data}
                filename = name_pattern

            # Output into variant subdirectory, preserving config subpath
            if isinstance(rel_output_dir, str):
                out_dir = variant_dir / rel_output_dir
            else:
                # ROOT_DIR case (docker-compose.yml) -> root of variant dir
                out_dir = variant_dir

            output_path = out_dir / filename
            generate_config(template, context, output_path)
            stats[config_name] += 1

        realm_context = {"stage": "latest", "gpu_enabled": gpu_enabled, "config_file_suffix": "", **config_data}
        generate_keycloak_realm(env, realm_context, variant_dir / "configs/keycloak/aihub-realm.json")
        stats["keycloak-realm"] = stats.get("keycloak-realm", 0) + 1

        # Copy static directories and files into the release bundle
        for src_rel, dst_rel in STATIC_COPY_DIRS:
            src_dir = DEPLOYMENT_DIR / src_rel
            dst_dir = variant_dir / dst_rel
            dst_dir.mkdir(parents=True, exist_ok=True)
            for f in src_dir.iterdir():
                if f.is_file() and not f.name.startswith("test_"):
                    shutil.copy2(f, dst_dir / f.name)

        for src_rel, dst_rel, filename in STATIC_COPY_FILES:
            src = DEPLOYMENT_DIR / src_rel
            dst = variant_dir / dst_rel / filename
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # Copy static files into the release bundle
        static_count = _copy_release_static_files(variant_dir)
        if static_count > 0:
            print(f"Copied {static_count} static files into {folder_name}/")
            stats["static-files"] = stats.get("static-files", 0) + static_count

    return stats


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Docker Compose configuration files")
    parser.add_argument(
        "--release",
        action="store_true",
        help="Generate release artifacts with version-pinned images",
    )
    parser.add_argument(
        "--project",
        metavar="NAME",
        default="swissaihub",
        help="Project name for release folder naming (default: swissaihub)",
    )
    parser.add_argument(
        "--tag",
        metavar="TAG",
        default="dev",
        help="Version tag for release artifacts (default: dev)",
    )
    parser.add_argument(
        "--output-dir",
        metavar="PATH",
        help="Output directory for release artifacts (default: project root)",
    )
    parser.add_argument(
        "--strict-env-check",
        action="store_true",
        help="Fail if .env.template defines unused vars or compose references undefined vars",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Run env/compose consistency check against .env.prod and rendered latest compose files (no generation)",
    )
    parser.add_argument(
        "--write-env-docs",
        action="store_true",
        help="Generate the environment-variables reference page in docs/",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    config_data = load_config()
    env = Environment(loader=FileSystemLoader(DEPLOYMENT_DIR), keep_trailing_newline=True)
    env.globals["service_license"] = _make_service_license_fn(_load_license_config())

    if args.check_env:
        from env_check import check_env_vs_compose
        from env_inventory import build_consumers

        env_file = REPO_ROOT / ".env.prod"
        compose_cpu = ROOT_DIR / "docker-compose.latest.yml"
        compose_gpu = ROOT_DIR / "docker-compose.latest.gpu.yml"
        if not compose_cpu.exists() or not compose_gpu.exists():
            print("ERROR: Run `make generate-compose` first to produce latest compose files", file=sys.stderr)
            sys.exit(1)
        consumers = build_consumers()
        # Run both variants non-strict so the report covers CPU AND GPU even
        # when one fails. Apply the strict-exit decision in aggregate:
        #   strict=True  → exit 1 if any variant has errors
        #   strict=False → always exit 0 (report-only, useful for local runs)
        ok_cpu = check_env_vs_compose(env_file, compose_cpu, consumers, "latest CPU", strict=False)
        ok_gpu = check_env_vs_compose(env_file, compose_gpu, consumers, "latest GPU", strict=False)
        all_ok = ok_cpu and ok_gpu
        sys.exit(1 if args.strict_env_check and not all_ok else 0)

    if args.write_env_docs:
        from env_docs import write_env_var_docs
        from env_inventory import build_consumers

        consumers = build_consumers()
        compose_variants = {
            "CPU": ROOT_DIR / "docker-compose.latest.yml",
            "GPU": ROOT_DIR / "docker-compose.latest.gpu.yml",
        }
        if not all(p.exists() for p in compose_variants.values()):
            print("ERROR: Run `make generate-compose` first to produce latest compose files", file=sys.stderr)
            sys.exit(1)
        docs_path = REPO_ROOT / "docs/docs/2_platform/3_deployment_guide/9_environment_variables/index.en.md"
        write_env_var_docs(docs_path, consumers, compose_variants)
        print(f"Wrote env-var docs to {docs_path.relative_to(REPO_ROOT)}")
        return

    if args.release:
        version = args.tag
        project = args.project
        output_dir = Path(args.output_dir) if args.output_dir else ROOT_DIR
        output_dir = output_dir.resolve()

        print(f"Generating release artifacts for {project} {version}...\n")
        stats = generate_release(env, config_data, version, output_dir, project)
    else:
        print("Generating configuration files...\n")
        stats = generate_default(env, config_data)

    # Print summary
    print(f"\nGeneration complete!")
    for name, count in stats.items():
        icon = "[]" if "docker-compose" in name else "  "
        print(f"   {icon} {count} {name} files")
    print(f"\nTotal: {sum(stats.values())} files generated")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise  # Show full traceback for debugging
