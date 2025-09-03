#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from aihub_cli import __version__


def get_package_version():
    """Get the version of the current package."""
    return __version__


def generate_docker_compose(output_path=None):
    """Generate docker-compose.yml from template."""
    try:
        # Get package version
        version = get_package_version()

        # Set up Jinja environment
        env = Environment(loader=PackageLoader("aihub_cli", "templates"), autoescape=select_autoescape(["html", "xml"]))

        # Load template
        template = env.get_template("docker-compose.yml.j2")

        # Render template with version
        rendered = template.render(version=version)

        # Determine output path
        if output_path is None:
            output_path = Path.cwd() / "docker-compose.yml"
        else:
            output_path = Path(output_path)

        # Write file
        output_path.write_text(rendered)

        print(f"Generated docker-compose.yml (version: {version}) at: {output_path}")
        return str(output_path)

    except Exception as e:
        raise RuntimeError(f"Failed to generate docker-compose.yml: {e}")


def main():
    parser = argparse.ArgumentParser(description="CLI tool for your package", prog="your-cli")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Docker-compose generation command
    compose_parser = subparsers.add_parser("generate-compose", help="Generate docker-compose.yml from template")
    compose_parser.add_argument(
        "-o", "--output", help="Output path for docker-compose.yml (default: ./docker-compose.yml)", default=None
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show package version")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "generate-compose":
            generate_docker_compose(args.output)
        elif args.command == "version":
            version = get_package_version()
            print(f"aihub version: {version}")
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
