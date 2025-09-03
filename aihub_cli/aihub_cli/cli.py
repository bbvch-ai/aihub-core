#!/usr/bin/env python3

"""Main CLI module using Click."""

import click
from aihub_cli import __version__


@click.group()
@click.version_option(version=__version__, prog_name="aihub-cli")
def cli():
    """CLI tool for AI-Hub development and deployment."""
    pass


@cli.command()
def version():
    """Show package version."""
    click.echo(f"aihub version: {__version__}")


def register_commands():
    """Register commands from separate modules."""
    # This approach avoids type issues by importing at runtime
    import importlib
    
    # Import and add commands dynamically
    compose_module = importlib.import_module("aihub_cli.commands.generate_compose")
    env_module = importlib.import_module("aihub_cli.commands.generate_env")
    
    cli.add_command(compose_module.generate_compose)
    cli.add_command(env_module.generate_env)


# Register commands
register_commands()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
