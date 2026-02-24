"""
Generates Docker Compose and service configuration files from Jinja2 templates.
Based on a matrix of stages (dev/local/nightly/latest) and hardware (CPU/GPU).

Supports a --release mode to generate self-contained deployment bundles with
version-pinned image tags and clean filenames (no stage/hardware suffixes).
"""

import argparse
import shutil
import sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

# Paths
ROOT_DIR = Path(__file__).parent.parent.resolve()
DEPLOYMENT_DIR = Path(__file__).parent.resolve()

# Stages and hardware variants
STAGES = ["dev", "local", "latest", "nightly", "build"]
GPU_MODES = {False: "", True: ".gpu"}

# Configuration specs: (template_path, output_dir, output_name_pattern)
CONFIG_SPECS = [
    # Docker Compose - always required
    ("templates/docker-compose.yml.j2", ROOT_DIR, "docker-compose.{stage}{hardware}.yml"),
    # Service configs - optional, skipped if template missing
    ("templates/configs/litellm-config.yml.j2", "configs/litellm", "litellm-config.{stage}{hardware}.yml"),
    ("templates/configs/milvus-config.yml.j2", "configs/milvus", "milvus-config.{stage}{hardware}.yml"),
    ("templates/configs/nats-config.conf.j2", "configs/nats", "nats-config.{stage}{hardware}.conf"),
    ("templates/configs/dagster-config.yml.j2", "configs/dagster", "dagster-config.{stage}{hardware}.yml"),
    ("templates/configs/workspace.yml.j2", "configs/dagster", "workspace.{stage}{hardware}.yml"),
    ("templates/configs/otel-config.yml.j2", "configs/otel", "otel-config.{stage}{hardware}.yml"),
    ("templates/configs/traefik-config.yml.j2", "configs/traefik", "traefik-config.{stage}{hardware}.yml"),
    ("templates/configs/traefik-middlewares.yml.j2", "configs/traefik", "middlewares.{stage}{hardware}.yml"),
    ("templates/configs/traefik-tls.yml.j2", "configs/traefik", "tls.{stage}{hardware}.yml"),
    # Static scripts - no stage/hardware variations
    ("templates/configs/init.Dockerfile.j2", "configs/etcd", "init.Dockerfile"),
    ("templates/configs/s3-entrypoint.sh.j2", "configs/seaweedfs", "s3-entrypoint.sh"),
    ("templates/configs/s3-init-buckets.sh.j2", "configs/seaweedfs", "init-buckets.sh"),
    ("templates/configs/pg-init-multiple-dbs.sh.j2", "configs/postgres", "init-multiple-dbs.sh"),
    ("templates/configs/openwebui-init-functions.sh.j2", "configs/openwebui", "init-functions.sh"),
    ("templates/configs/init_etcd.sh.j2", "configs/etcd", "init_etcd.sh"),
]

# Additional static files included only in release bundles (non-config files).
# Config files are copied automatically from ROOT_DIR/configs/.
# (source relative to ROOT_DIR, destination relative to variant_dir)
RELEASE_STATIC_FILES = [
    (".env.prod", ".env.template"),
    ("setup-env.py", "setup-env.py"),
]


def load_config():
    """Load compose-config.yml"""
    config_path = DEPLOYMENT_DIR / "compose-config.yml"
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_template(env, template_path):
    """Load a Jinja2 template, return None if not found"""
    return env.get_template(template_path)


def generate_config(template, context, output_path):
    """Render template and write to file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = template.render(context)
    output_path.write_text(rendered, encoding="utf-8")


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
    """
    image_tags = config_data.get("image_tags", {})
    for service, tag_value in image_tags.items():
        if isinstance(tag_value, dict) and "latest" in tag_value:
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

    return stats


def _release_compose_header(project, version, gpu_enabled):
    """Build the header comment block for release compose files."""
    variant = "GPU-enabled" if gpu_enabled else "CPU-only"
    return (
        f"# {project} {version} - Docker Compose Configuration ({variant})\n"
        f"#\n"
        f"# This is the {'GPU-enabled' if gpu_enabled else 'CPU-only (no GPU)'} deployment configuration.\n"
        + (
            f"# It includes GPU-accelerated services such as vLLM and Speaches.\n"
            if gpu_enabled
            else f"# GPU-accelerated services are excluded from this configuration.\n"
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

    # Copy non-config release files (.env.template, setup-env.py)
    for src_rel, dst_rel in RELEASE_STATIC_FILES:
        src = ROOT_DIR / src_rel
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
    return parser.parse_args()


def main():
    args = parse_args()

    config_data = load_config()
    env = Environment(loader=FileSystemLoader(DEPLOYMENT_DIR))

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
