import importlib.metadata
from pathlib import Path
import toml


def get_version():
    """Get package version from multiple sources."""
    try:
        # Try getting from installed package metadata
        return importlib.metadata.version("your-package")
    except importlib.metadata.PackageNotFoundError:
        try:
            # Fallback: read from pyproject.toml in development
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path) as f:
                    pyproject = toml.load(f)
                    return pyproject["tool"]["poetry"]["version"]
        except Exception:
            pass

        # Final fallback
        return "dev"


__version__ = get_version()
