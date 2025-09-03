"""Environment file generation command."""

import re
import secrets
from pathlib import Path
from typing import Optional
from jinja2 import Environment, PackageLoader, select_autoescape
import click


@click.command("generate-env")
@click.option("-o", "--output", type=click.Path(), help="Output path for .env file (default: ./.env.core)")
def generate_env(output: Optional[str]) -> Optional[str]:
    """Generate .env.core file by extracting environment variables from rendered template."""

    # Environment variables that should get random hex values instead of generic placeholders
    HEX_VALUE_VARS = {
        # 32-character hex values (secrets/keys)
        "AUTH_OPEN_WEBUI_SIGNING_SECRET": 32,
        "LITELLM_MASTER_KEY": 32,
        "LITELLM_UI_PASSWORD": 32,
        "MINIO_ROOT_PASSWORD": 32,
        "MONGO_PASSWORD": 32,
        "POSTGRES_PASSWORD": 32,
        "SUPERUSER_TOKEN": 32,
        # 16-character hex values (shorter secrets)
        "OAUTH_COOKIE_SECRET": 16,
        "SUPERUSER_OID": 16,
    }

    # Environment variables with custom default values
    CUSTOM_DEFAULT_VARS = {
        "LITELLM_UI_USERNAME": "admin",
        "LOG_LEVEL": "DEBUG",
        "MINIO_ROOT_USER": "admin",
        "MONGO_USERNAME": "admin",
        "POSTGRES_USER": "admin",
        "SUPERUSER_EMAIL": "superuser@ai-hub.bbv.ch",
        "SUPERUSER_NAME": "AI-Hub Superuser",
    }

    try:
        # Set up Jinja environment
        env = Environment(
            loader=PackageLoader(package_name="aihub_cli", package_path="templates"),
            autoescape=select_autoescape(enabled_extensions=["html", "xml"]),
        )

        # Load and render template with dummy version
        template = env.get_template(name="docker-compose.dev.yml.j2")
        rendered = template.render(version="latest")

        # Extract environment variables using regex
        env_vars = set()
        # Match ${VAR_NAME} and $VAR_NAME patterns
        patterns = [
            r"\$\{([A-Z_][A-Z0-9_]*)\}",
            r"\$([A-Z_][A-Z0-9_]*)(?![A-Z0-9_])",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, rendered)
            env_vars.update(matches)

        # Determine output path
        if output is None:
            output_path = Path.cwd() / ".env.core"
        else:
            output_path = Path(output)

        # Generate simple .env content
        content_lines = [
            "# =============================================================================",
            "# AI-Hub Core Environment Variables",
            "# Generated from docker-compose template",
            "# =============================================================================",
            "",
        ]

        # Add all found variables with placeholder values, grouped by prefix
        sorted_vars = sorted(env_vars)
        previous_prefix = None

        for var in sorted_vars:
            # Get the prefix (part before first underscore)
            current_prefix = var.split("_")[0] if "_" in var else var

            # Add empty line if prefix changed (except for first variable)
            if previous_prefix is not None and current_prefix != previous_prefix:
                content_lines.append("")

            # Generate appropriate value based on variable type
            if var in HEX_VALUE_VARS:
                # Generate random hex value of specified length
                hex_length = HEX_VALUE_VARS[var]
                hex_value = secrets.token_hex(hex_length)
                content_lines.append(f"{var}={hex_value}")
            elif var in CUSTOM_DEFAULT_VARS:
                # Use custom default value
                content_lines.append(f"{var}={CUSTOM_DEFAULT_VARS[var]}")
            else:
                # Use generic placeholder
                content_lines.append(f"{var}=[your_{var.lower()}_here]")

            previous_prefix = current_prefix

        content = "\n".join(content_lines) + "\n"

        # Write file
        output_path.write_text(data=content)

        click.echo(f"Generated .env.core with {len(env_vars)} variables at: {output_path}")
        return str(output_path)

    except Exception as e:
        raise click.ClickException(f"Failed to generate .env.core file: {e}")
