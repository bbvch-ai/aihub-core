"""
Generates Docker Compose and service configuration files from Jinja2 templates.
Based on a matrix of stages (dev/local/nightly/latest) and hardware (CPU/GPU).
"""

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
    # Keycloak configs - realm (platform) and identity providers (customer)
    ("templates/configs/keycloak-realm.json.j2", "configs/keycloak", "aihub-realm.{stage}{hardware}.json"),
    ("templates/configs/keycloak-identity-providers.json.j2", "configs/keycloak", "identity-providers.{stage}{hardware}.json"),
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


def main():
    print("🚀 Generating configuration files...\n")

    # Load data and setup Jinja2
    config_data = load_config()
    env = Environment(loader=FileSystemLoader(DEPLOYMENT_DIR))

    # Track what we're generating
    stats = {}

    # Process each config spec
    for template_path, output_dir, name_pattern in CONFIG_SPECS:
        template = load_template(env, template_path)

        if not template:
            print(f"⚠️  Skipping {template_path} (not found)")
            continue

        config_name = template_path.split("/")[-1].replace(".j2", "").replace("-config", "")
        stats[config_name] = 0

        print(f"✅ Loaded template: {template_path}")

        # Determine output directory
        out_dir = ROOT_DIR / output_dir if isinstance(output_dir, str) else output_dir

        # Check if pattern has stage/hardware variables
        needs_stage_hardware = "{stage}" in name_pattern or "{hardware}" in name_pattern

        if needs_stage_hardware:
            # Generate for each stage × hardware combination
            for gpu_enabled, hardware in GPU_MODES.items():
                for stage in STAGES:
                    context = {"stage": stage, "gpu_enabled": gpu_enabled, **config_data}
                    filename = name_pattern.format(hardware=hardware, stage=stage)
                    output_path = out_dir / filename

                    generate_config(template, context, output_path)
                    stats[config_name] += 1
        else:
            # Generate single file (no stage/hardware variations)
            context = {"stage": "default", "gpu_enabled": False, **config_data}
            output_path = out_dir / name_pattern

            generate_config(template, context, output_path)
            stats[config_name] += 1

    # Copy OpenWebUI functions to configs directory
    functions_src = DEPLOYMENT_DIR / "templates" / "openwebui_functions"
    functions_dst = ROOT_DIR / "configs" / "openwebui" / "functions"
    if functions_src.exists():
        functions_dst.mkdir(parents=True, exist_ok=True)
        function_count = 0
        for py_file in functions_src.glob("*.py"):
            shutil.copy2(py_file, functions_dst / py_file.name)
            function_count += 1
        if function_count > 0:
            print(f"✅ Copied {function_count} OpenWebUI functions to configs/openwebui/functions/")
            stats["openwebui-functions"] = function_count

    # Print summary
    print(f"\n✨ Generation complete!")
    for name, count in stats.items():
        icon = "📦" if "docker-compose" in name else "🔧"
        print(f"   {icon} {count} {name} files")
    print(f"\n📊 Total: {sum(stats.values())} files generated")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ ERROR: Invalid YAML in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        raise  # Show full traceback for debugging
