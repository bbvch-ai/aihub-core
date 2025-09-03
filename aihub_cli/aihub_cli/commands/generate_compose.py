"""Docker Compose generation command."""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader, select_autoescape
import click
from aihub_cli import __version__


def get_package_version():
    """Get the version of the current package."""
    return __version__


@click.command("generate-compose")
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output path for docker-compose.yml (default: ./docker-compose-core.dev.yml)",
)
@click.option(
    "--tag", type=click.Choice(["nightly", "latest"]), help="Use 'nightly' or 'latest' tag instead of package version"
)
def generate_compose(output: Optional[str], tag: Optional[str]) -> str:
    """Generate docker-compose.yml from template."""
    try:
        # Determine version/tag to use
        if tag in ["nightly", "latest"]:
            version = tag
        else:
            version = get_package_version()

        # Set up Jinja environment
        env = Environment(
            loader=PackageLoader(package_name="aihub_cli", package_path="templates"),
            autoescape=select_autoescape(enabled_extensions=["html", "xml"]),
        )

        # Load template
        template = env.get_template(name="docker-compose.dev.yml.j2")

        # Render template with version
        rendered = template.render(version=version)

        # Determine output path
        if output is None:
            output_path = Path.cwd() / "docker-compose-core.dev.yml"
        else:
            output_path = Path(output)

        # Write file
        output_path.write_text(data=rendered)

        click.echo(f"Generated docker-compose.yml (version: {version}) at: {output_path}")
        return str(output_path)

    except Exception as e:
        raise click.ClickException(f"Failed to generate docker-compose.yml: {e}")
