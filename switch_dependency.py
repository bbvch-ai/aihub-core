"""
A script to switch each microservice's 'aihub_lib' dependency between
a local path and a remote Git reference, using tomlkit to preserve the
existing file structure.

It specifically looks for pyproject.toml in:
  - aihub_agent/
  - aihub_api/
  - aihub_bot/
  - aihub_pipeline/

Usage:
  python switch_dependency.py [local|remote] [--tag <TAG>] [--local-path <PATH>]

Examples:
  # Switch to local references (default path="../aihub_lib")
  python switch_dependency.py local

  # Switch to remote references (default tag="v0.1.0")
  python switch_dependency.py remote

  # Switch to remote references with a custom Git tag
  python switch_dependency.py remote --tag v0.2.0
"""

import argparse
import subprocess
from pathlib import Path

import sys

try:
    import tomlkit
except ImportError:
    print(
        "ERROR: Missing 'tomlkit' library.\n"
        "Install it with:\n  poetry add --group dev tomlkit\n"
        "or:\n  pip install tomlkit\n"
    )
    sys.exit(1)

MICROSERVICE_DIRS = [
    "aihub_agent",
    "aihub_api",
    "aihub_bot",
    "aihub_pipeline",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Toggle 'aihub_lib' between local and remote references "
        "for specified microservice folders (using tomlkit)."
    )
    parser.add_argument(
        "mode",
        choices=["local", "remote"],
        help="Use 'local' for a local path reference, or 'remote' for a Git reference.",
    )
    parser.add_argument(
        "--tag",
        default="v0.1.0",
        help="Git tag (or branch) to use when in 'remote' mode. (Default: v0.1.0)",
    )
    parser.add_argument(
        "--local-path",
        default="../aihub_lib",
        help="Local path to the aihub_lib for 'local' mode. (Default: ../aihub_lib)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).resolve().parent

    for folder in MICROSERVICE_DIRS:
        folder_path = repo_root / folder
        pyproject_path = folder_path / "pyproject.toml"

        if not pyproject_path.is_file():
            continue

        process_file(
            pyproject_path=pyproject_path,
            mode=args.mode,
            local_path=args.local_path,
            remote_tag=args.tag,
        )


def process_file(pyproject_path: Path, mode: str, local_path: str, remote_tag: str):
    original_text = pyproject_path.read_text(encoding="utf-8")
    doc = tomlkit.parse(original_text)

    update_aihub_lib(doc, mode, local_path, remote_tag)
    pyproject_path.write_text(tomlkit.dumps(doc), encoding="utf-8")

    subprocess.run(["poetry", "lock"], cwd=pyproject_path.parent)


def update_aihub_lib(doc: tomlkit.container.Container, mode: str, local_path: str, remote_tag: str):
    if "tool" not in doc or "poetry" not in doc["tool"]:
        return

    poetry_section = doc["tool"]["poetry"]
    if "dependencies" not in poetry_section:
        return

    deps = poetry_section["dependencies"]
    if "aihub_lib" not in deps:
        return

    if mode == "local":
        new_dep = {
            "path": local_path,
            "develop": True,
        }
    else:
        new_dep = {
            "git": "https://github.com/bbvch-ai/aihub-core.git",
            "tag": remote_tag,
            "subdirectory": "aihub_lib",
        }

    deps["aihub_lib"] = new_dep


if __name__ == "__main__":
    main()
