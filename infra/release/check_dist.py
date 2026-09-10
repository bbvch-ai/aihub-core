"""Validate built distribution artifacts before publishing to PyPI.

Run against a ``dist/`` directory of wheels and sdists. Two hard checks per artifact:

  1. **Namespace integrity** — the shared ``swiss_ai_hub`` namespace MUST remain a PEP 420
     native namespace. Any distribution that ships ``swiss_ai_hub/__init__.py`` claims the
     namespace as a regular package and silently breaks ``import`` for every sibling
     distribution. Each artifact must also actually ship a ``swiss_ai_hub/<sub>/`` module.
  2. **No leaked secrets** — fail if an artifact bundles credentials, key material, or VCS
     metadata that must never reach a public index.

Exit code is non-zero when any artifact fails, so this doubles as a CI gate.

    uv run python infra/release/check_dist.py            # checks ./dist
    uv run python infra/release/check_dist.py path/to/dist
"""

import argparse
import fnmatch
import re
import sys
import tarfile
import zipfile
from pathlib import Path

# A path whose components end in ``swiss_ai_hub/__init__.py`` — matches both the wheel
# layout (``swiss_ai_hub/__init__.py``) and the sdist layout (``<name>-<ver>/swiss_ai_hub/...``).
_NAMESPACE_INIT = re.compile(r"(^|/)swiss_ai_hub/__init__\.py$")
_NAMESPACE_SUBMODULE = re.compile(r"(^|/)swiss_ai_hub/[^/]+/__init__\.py$")

# Files that must never ship in a public artifact.
_SECRET_BASENAMES = {".env", ".pypirc", ".npmrc", ".netrc", "id_rsa", "id_dsa", "credentials"}
_SECRET_GLOBS = (".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.keystore", "*.pwd")
_SECRET_PATH_FRAGMENTS = ("/.git/", "/.ssh/", "/.aws/", "/secrets/")

_LARGE_FILE_BYTES = 5 * 1024 * 1024


class DistChecker:
    """Inspects wheels and sdists for namespace integrity and leaked secrets."""

    @staticmethod
    def members(artifact: Path) -> list[tuple[str, int]]:
        """Return ``(member_path, size)`` pairs for every file in the artifact."""
        if artifact.suffix == ".whl" or artifact.name.endswith(".zip"):
            with zipfile.ZipFile(artifact) as archive:
                return [(info.filename, info.file_size) for info in archive.infolist() if not info.is_dir()]
        with tarfile.open(artifact) as archive:
            return [(member.name, member.size) for member in archive.getmembers() if member.isfile()]

    @staticmethod
    def is_secret(member_path: str) -> bool:
        basename = member_path.rsplit("/", 1)[-1]
        if basename in _SECRET_BASENAMES:
            return True
        if any(fnmatch.fnmatch(basename, pattern) for pattern in _SECRET_GLOBS):
            return True
        normalized = f"/{member_path}"
        return any(fragment in normalized for fragment in _SECRET_PATH_FRAGMENTS)

    @classmethod
    def check_artifact(cls, artifact: Path) -> list[str]:
        """Return a list of human-readable failures for one artifact (empty == passed)."""
        members = cls.members(artifact)
        paths = [path for path, _ in members]
        failures: list[str] = []

        if any(_NAMESPACE_INIT.search(path) for path in paths):
            failures.append("ships swiss_ai_hub/__init__.py — breaks the PEP 420 namespace for the whole family")
        if not any(_NAMESPACE_SUBMODULE.search(path) for path in paths):
            failures.append("contains no swiss_ai_hub/<submodule>/ package — nothing importable shipped")

        for path in paths:
            if cls.is_secret(path):
                failures.append(f"bundles a secret-looking file: {path}")
        for path, size in members:
            if size > _LARGE_FILE_BYTES:
                failures.append(f"unexpectedly large file ({size // 1024} KiB): {path}")

        return failures

    @classmethod
    def check_dist(cls, dist_dir: Path) -> bool:
        """Check every wheel/sdist in ``dist_dir``. Returns True if all passed."""
        artifacts = sorted(p for p in dist_dir.glob("*") if p.suffix in {".whl", ".gz"} or p.name.endswith(".tar.gz"))
        if not artifacts:
            print(f"ERROR: no .whl or .tar.gz artifacts found in {dist_dir}")
            return False

        all_ok = True
        print(f"Checking {len(artifacts)} artifact(s) in {dist_dir}\n")
        for artifact in artifacts:
            failures = cls.check_artifact(artifact)
            if failures:
                all_ok = False
                print(f"  FAIL  {artifact.name}")
                for failure in failures:
                    print(f"          - {failure}")
            else:
                print(f"  OK    {artifact.name}")

        print()
        print("All artifacts passed." if all_ok else "One or more artifacts FAILED — do not publish.")
        return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PyPI distribution artifacts.")
    parser.add_argument("dist_dir", nargs="?", default="dist", help="Directory of built artifacts (default: ./dist)")
    args = parser.parse_args()

    dist_dir = Path(args.dist_dir)
    if not dist_dir.is_dir():
        print(f"ERROR: {dist_dir} is not a directory")
        return 1
    return 0 if DistChecker.check_dist(dist_dir) else 1


if __name__ == "__main__":
    sys.exit(main())
