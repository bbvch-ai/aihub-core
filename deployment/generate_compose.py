"""
This script generates multiple Docker Compose files based on a matrix of stages
and hardware configurations (CPU/GPU) using a Jinja2 template.
"""

import sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT_DIR = Path(__file__).parent.parent.resolve()
DEPLOYMENT_DIR = Path(__file__).parent.resolve()
TEMPLATE_FILE = "docker-compose.yml.j2"
CONFIG_FILE = "compose-config.yml"

STAGES = ["dev", "local", "latest", "nightly"]
GPU_MODES = {False: "", True: "gpu."}


def generate_files():
    """
    Loads configuration and templates, then iterates through the matrix
    to generate all required docker-compose files.
    """
    print("🚀 Starting Docker Compose file generation...")

    # --- 1. Load Configuration Data ---
    config_path = DEPLOYMENT_DIR / CONFIG_FILE
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        print(f"✅ Successfully loaded config from: {config_path}")
    except FileNotFoundError:
        print(f"❌ FATAL: Config file not found at '{config_path}'. Please ensure it exists.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ FATAL: Error parsing YAML config file '{config_path}': {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Set up Jinja2 Environment ---
    env = Environment(loader=FileSystemLoader(DEPLOYMENT_DIR))
    try:
        template = env.get_template(TEMPLATE_FILE)
        print(f"✅ Successfully loaded Jinja2 template from: {DEPLOYMENT_DIR / TEMPLATE_FILE}")
    except Exception as e:
        print(f"❌ FATAL: Could not load Jinja2 template '{TEMPLATE_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

    # --- 3. Generate Files for Each Combination ---
    generated_count = 0
    for gpu_enabled, prefix in GPU_MODES.items():
        for stage in STAGES:
            # Output files are placed in the root directory.
            output_filename = f"docker-compose.{prefix}{stage}.yml"
            output_path = ROOT_DIR / output_filename

            # The context dictionary provides data to the template.
            context = {
                "stage": stage,
                "gpu_enabled": gpu_enabled,
                **config_data,  # Unpack all loaded config data into the context
            }

            try:
                # Render the template with the specific context for this file.
                rendered_content = template.render(context)

                # Write the rendered content to the output file.
                with output_path.open("w", encoding="utf-8") as f:
                    f.write(rendered_content)

                print(f"  📄 Generated: {output_path.name}")
                generated_count += 1
            except Exception as e:
                print(
                    f"❌ ERROR: Failed to render or write for stage='{stage}', gpu={gpu_enabled}: {e}", file=sys.stderr
                )

    print(f"\n✨ Generation complete. {generated_count} files created successfully.")


if __name__ == "__main__":
    generate_files()
