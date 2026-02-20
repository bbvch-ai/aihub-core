"""
Swiss AI Hub - Environment Setup Script

Reads .env.template and generates a .env file with auto-generated secrets
for all values that can be safely randomized (database passwords, tokens,
signing keys, etc.).

Values that require manual configuration (domain, API keys, OAuth settings)
are left unchanged for the operator to fill in.

Usage:
    python setup-env.py                     # generates .env from .env.template
    python setup-env.py -o custom.env       # write to a custom output file
    python setup-env.py --force             # overwrite existing .env
"""

import argparse
import secrets
import sys
from pathlib import Path

# Placeholder patterns and their generators
GENERATORS = {
    "REPLACE_WITH_RANDOM_STRING": lambda: secrets.token_urlsafe(32),
    "REPLACE_WITH_64_HEX_CHARS": lambda: secrets.token_hex(32),
    "pk-lf-REPLACE_WITH_LANGFUSE_PUBLIC_KEY": lambda: f"pk-lf-{secrets.token_urlsafe(24)}",
    "sk-lf-REPLACE_WITH_LANGFUSE_SECRET_KEY": lambda: f"sk-lf-{secrets.token_urlsafe(24)}",
}


def generate_env(template_path: Path, output_path: Path) -> dict[str, int]:
    """Read the template, replace auto-generatable placeholders, write output."""
    content = template_path.read_text(encoding="utf-8")

    stats: dict[str, int] = {}
    for placeholder, generator in GENERATORS.items():
        count = content.count(placeholder)
        if count > 0:
            # Each occurrence gets its own unique value
            for _ in range(count):
                content = content.replace(placeholder, generator(), 1)
            stats[placeholder] = count

    output_path.write_text(content, encoding="utf-8")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate .env from .env.template with auto-generated secrets")
    parser.add_argument(
        "-t", "--template",
        default=".env.template",
        help="Path to the template file (default: .env.template)",
    )
    parser.add_argument(
        "-o", "--output",
        default=".env",
        help="Path to the output file (default: .env)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists",
    )
    args = parser.parse_args()

    template_path = Path(args.template)
    output_path = Path(args.output)

    if not template_path.exists():
        print(f"ERROR: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    if output_path.exists() and not args.force:
        print(f"ERROR: Output file already exists: {output_path}", file=sys.stderr)
        print("       Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    stats = generate_env(template_path, output_path)

    total = sum(stats.values())
    print(f"Generated {output_path} from {template_path}")
    print(f"  {total} secrets auto-generated:")
    for placeholder, count in stats.items():
        print(f"    {count}x {placeholder}")
    print()
    print("Review the file and fill in the remaining values marked with REPLACE_WITH_*.")


if __name__ == "__main__":
    main()
