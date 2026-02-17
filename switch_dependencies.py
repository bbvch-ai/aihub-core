"""
A script to switch each microservice's in-project dependencies between
a local path and a remote Git reference, using tomlkit to preserve the
existing file structure.

It specifically looks for pyproject.toml in:
  - aihub_agent/
  - aihub_api/
  - aihub_bot/
  - aihub_pipeline/
  - aihub_process/

Usage:
  python switch_dependencies.py [local|remote] [--tag <TAG>] [--install]

Examples:
  # Switch to local references without installing
  python switch_dependencies.py local

  # Switch to local references and run poetry install
  python switch_dependencies.py local --install

  # Switch to remote references (default tag="v0.1.0") without installing
  python switch_dependencies.py remote

  # Switch to remote references with a custom Git tag and install
  python switch_dependencies.py remote --tag v0.2.0 --install
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
    "aihub_lib",
    "aihub_agent",
    "aihub_api",
    "aihub_bot",
    "aihub_pipeline",
    "aihub_process",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Toggle dependencies between local and remote references "
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
        "--install",
        action="store_true",
        help="Run poetry lock and poetry install after updating dependencies",
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
            remote_tag=args.tag,
            run_install=args.install,
        )


def _venv_exists(scope_dir: Path) -> bool:
    """Check if a Poetry virtualenv exists for this scope."""
    # Check in-project .venv first (most common with poetry config virtualenvs.in-project true)
    if (scope_dir / ".venv" / "bin" / "python").exists():
        return True
    # Fall back to asking Poetry (slower, ~1s)
    result = subprocess.run(
        ["poetry", "env", "info", "--path"],
        cwd=scope_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and Path(result.stdout.strip()).is_dir()


def process_file(pyproject_path: Path, mode: str, remote_tag: str, run_install: bool):
    original_text = pyproject_path.read_text(encoding="utf-8")
    doc = tomlkit.parse(original_text)

    for dependency_name in MICROSERVICE_DIRS:
        update_dependency(doc, mode, remote_tag, dependency_name)

    new_text = tomlkit.dumps(doc)
    scope_name = pyproject_path.parent.name
    lock_path = pyproject_path.parent / "poetry.lock"
    pyproject_unchanged = new_text == original_text

    # Skip if pyproject.toml didn't change, lock file exists, and venv is present
    if pyproject_unchanged and lock_path.exists() and run_install:
        if _venv_exists(pyproject_path.parent):
            print(f"⏭️  {scope_name}: Already up to date, skipping.")
            return
        else:
            print(f"🔄 {scope_name}: venv missing, reinstalling...")

    if not pyproject_unchanged:
        pyproject_path.write_text(new_text, encoding="utf-8")
        print(f"✅ Updated {pyproject_path}")
    else:
        print(f"✅ {scope_name}: pyproject.toml already in {mode} mode.")

    # Only run poetry commands if --install flag is set
    if run_install:
        print(f"📦 Running poetry lock for {scope_name}...")
        result = subprocess.run(["poetry", "lock"], cwd=pyproject_path.parent, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            print(f"❌ Failed to lock dependencies in {pyproject_path.parent}")
            if result.stderr:
                print(f"stderr: {result.stderr}")
            sys.exit(1)

        print(f"📦 Running poetry install for {scope_name}...")
        if mode == "local":
            result = subprocess.run(
                ["poetry", "install", "--with", "dev"], cwd=pyproject_path.parent, capture_output=True, text=True
            )
        else:
            result = subprocess.run(["poetry", "install"], cwd=pyproject_path.parent, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            print(f"❌ Failed to install dependencies in {pyproject_path.parent}")
            if result.stderr:
                print(f"stderr: {result.stderr}")
            sys.exit(1)
        print(f"✅ Successfully installed dependencies for {scope_name}")
    else:
        print(f"ℹ️  Skipping poetry lock/install for {scope_name} (--install flag not set)")


def update_dependency(doc: tomlkit.container.Container, mode: str, remote_tag: str, dependency_name: str):
    if "tool" not in doc or "poetry" not in doc["tool"]:
        return

    poetry_section = doc["tool"]["poetry"]
    if "dependencies" not in poetry_section:
        return

    deps = poetry_section["dependencies"]
    if dependency_name not in deps:
        return

    if mode == "local":
        new_dep = {
            "path": f"../{dependency_name}",
            "develop": True,
        }
    else:
        new_dep = {
            "git": "https://github.com/bbvch-ai/aihub-core.git",
            "tag": remote_tag,
            "subdirectory": dependency_name,
        }

    deps[dependency_name] = new_dep


if __name__ == "__main__":
    main()
