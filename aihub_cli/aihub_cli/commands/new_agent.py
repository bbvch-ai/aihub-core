"""New agent creation command."""

import re
from pathlib import Path
from typing import Optional

import click
from jinja2 import Environment, PackageLoader, select_autoescape


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to CamelCase.

    Args:
        snake_str: String in snake_case format

    Returns:
        String in CamelCase format
    """
    components = snake_str.split("_")
    return "".join(word.capitalize() for word in components)


def validate_agent_name(agent_name: str) -> None:
    """Validate the agent name format.

    Args:
        agent_name: The agent name to validate

    Raises:
        click.ClickException: If the agent name is invalid
    """
    if not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]$", agent_name):
        raise click.ClickException(
            "Agent name must be in snake_case format, start with a lowercase letter, "
            "and contain only lowercase letters, numbers, and underscores."
        )


@click.command("new-agent")
@click.argument("agent_name", type=str)
@click.option(
    "--agents-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    default="agents",
    help="Directory where agents are stored (default: agents)",
)
def new_agent(agent_name: str, agents_dir: Optional[str]) -> None:
    """Create a new AI agent with the specified name.

    Creates the complete agent structure with all necessary files:
    - pyproject.toml with dependencies
    - Dockerfile for containerization
    - main.py entry point
    - Agent implementation class
    - Agent configuration class
    - Events directory for custom events

    Args:
        agent_name: Name of the agent in snake_case format (e.g., 'my_custom_agent')
        agents_dir: Directory where agents are stored
    """
    try:
        validate_agent_name(agent_name)

        agents_path = Path(agents_dir or "agents")
        agent_path = agents_path / agent_name

        if not agents_path.exists():
            if click.confirm(f"The directory '{agents_path}' does not exist. Create it?"):
                agents_path.mkdir(parents=True, exist_ok=True)
                click.echo(f"Created agents directory: {agents_path}")
            else:
                raise click.ClickException("Agent creation cancelled.")

        if agent_path.exists():
            raise click.ClickException(f"Agent '{agent_name}' already exists at {agent_path}")

        agent_class_name = to_camel_case(agent_name)

        env = Environment(
            loader=PackageLoader(package_name="aihub_cli", package_path="templates"),
            autoescape=select_autoescape(enabled_extensions=["html", "xml"]),
        )

        context = {
            "agent_name": agent_name,
            "agent_class_name": agent_class_name,
        }

        # Create agent directory structure
        agent_path.mkdir(parents=True, exist_ok=True)
        agent_class_path = agent_path / agent_class_name
        agent_class_path.mkdir(parents=True, exist_ok=True)
        events_path = agent_class_path / "events"
        events_path.mkdir(parents=True, exist_ok=True)

        # Create files from templates
        files_to_create = [
            # Root level files
            ("agent_pyproject.toml.j2", agents_path / "pyproject.toml"),
            ("agent_dockerfile.j2", agent_path / "Dockerfile"),
            ("agent_main.py.j2", agent_path / "main.py"),
            # Agent class files
            ("agent_class.py.j2", agent_class_path / f"{agent_class_name}.py"),
            ("agent_config.py.j2", agent_class_path / f"{agent_class_name}Config.py"),
        ]

        for template_name, output_path in files_to_create:
            template = env.get_template(template_name)
            content = template.render(**context)
            output_path.write_text(content, encoding="utf-8")
            click.echo(f"Created: {output_path}")

        # Create __init__.py files
        init_files = [
            agent_path / "__init__.py",
            agent_class_path / "__init__.py",
            events_path / "__init__.py",
        ]

        for init_file in init_files:
            init_file.write_text("", encoding="utf-8")
            click.echo(f"Created: {init_file}")

        click.echo(f"\n✅ Successfully created agent '{agent_name}' at {agent_path}")
        click.echo(f"\nAgent structure:")
        click.echo(f"├── {agents_path}/")
        click.echo(f"│   ├── pyproject.toml")
        click.echo(f"│   └── {agent_name}/")
        click.echo(f"│       ├── Dockerfile")
        click.echo(f"│       ├── main.py")
        click.echo(f"│       └── {agent_class_name}/")
        click.echo(f"│           ├── {agent_class_name}.py")
        click.echo(f"│           ├── {agent_class_name}Config.py")
        click.echo(f"│           └── events/")
        click.echo(f"\nNext steps:")
        click.echo(f"1. cd {agents_path}")
        click.echo(f"2. poetry install")
        click.echo(f"3. Customize your agent implementation in {agent_class_name}/{agent_class_name}.py")

    except Exception as e:
        raise click.ClickException(f"Failed to create agent: {e}")
