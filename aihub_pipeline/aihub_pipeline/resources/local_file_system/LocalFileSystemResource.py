import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.SourceFile import MinimalSourceFile, SourceFile


@dataclass
class ScanConfig:
    """Compiled regex patterns for file scanning."""

    include_patterns: Annotated[list[re.Pattern] | None, Field(description="Regex patterns for file paths to include.")]
    exclude_patterns: Annotated[list[re.Pattern] | None, Field(description="Regex patterns for file paths to exclude.")]


class LocalFileSystemResource(ConfigurableResource):
    """
    Scans local file systems using regex patterns for flexible filtering.

    Tip: Use helper functions from aihub_pipeline.util.pattern_utils:
    - exact_match_pattern(["A", "B"]) -> '^(A|B)$'
    - extension_pattern([".pdf", ".docx"]) -> '\\.(pdf|docx)$'
    - contains_pattern("archive") -> '.*archive.*'
    """

    base_path: Annotated[str, Field(description="Base path to start scanning from")]

    include_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Regex patterns for file paths to include (matched against relative path). "
            "None = include all files. Patterns are case-insensitive.",
        ),
    ]

    exclude_patterns: Annotated[
        list[str] | None,
        Field(
            default_factory=lambda: [r".*archiv.*"],
            description="Regex patterns for file paths to exclude (matched against relative path). "
            "Applied after include_patterns. Patterns are case-insensitive.",
        ),
    ]

    _scan_config: ScanConfig | None = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        self._scan_config = self._compile_patterns()

    def _compile_patterns(self) -> ScanConfig:
        """Compile all regex patterns once during initialization."""

        def compile_optional(patterns: list[str] | None) -> list[re.Pattern] | None:
            if patterns is None:
                return None
            return [re.compile(p, re.IGNORECASE) for p in patterns]

        return ScanConfig(
            include_patterns=compile_optional(self.include_patterns),
            exclude_patterns=compile_optional(self.exclude_patterns),
        )

    def fetch_all_files(self) -> list[MinimalSourceFile]:
        """Fetch all files matching configured patterns."""
        base = Path(self.base_path)

        if not base.exists():
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")

        return self._scan_recursively(directory=base)

    def _scan_recursively(self, directory: Path) -> list[MinimalSourceFile]:
        """Recursively scan directory for matching files."""
        files = []

        for item in directory.rglob("*"):
            if item.is_file():
                if file := self._process_file(file_path=item):
                    files.append(file)

        return files

    def _process_file(self, file_path: Path) -> MinimalSourceFile | None:
        """Process a single file if it passes all filters."""
        relative_path = file_path.relative_to(self.base_path).as_posix()

        if not self._should_include_file(relative_path=relative_path):
            return None

        stat = file_path.stat()

        return MinimalSourceFile(
            name=file_path.name,
            path=relative_path,
            size=stat.st_size,
            modified=int(stat.st_mtime),
        )

    def _should_include_file(self, relative_path: str) -> bool:
        """
        Check if file passes all inclusion filters.
        """
        # Handle include patterns
        if self._scan_config.include_patterns is not None:
            if not self._scan_config.include_patterns:  # Empty list = include nothing
                return False
            if not self._matches_any(text=relative_path, patterns=self._scan_config.include_patterns):
                return False

        # Handle exclude patterns (None and [] both mean "no exclusions")
        if self._scan_config.exclude_patterns:
            if self._matches_any(text=relative_path, patterns=self._scan_config.exclude_patterns):
                return False

        return True

    @staticmethod
    def _matches_any(text: str, patterns: list[re.Pattern] | None) -> bool:
        """Check if text matches any pattern in the list."""
        if patterns is None:
            return False
        if not patterns:
            return False
        return any(pattern.search(text) for pattern in patterns)

    def get_local_file(self, file_path: str) -> SourceFile:
        """Get a single file with content by relative path."""
        full_path = Path(self.base_path) / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {full_path}")

        with open(full_path, "rb") as f:
            content = f.read()

        stat = full_path.stat()
        content_type, _ = mimetypes.guess_type(full_path.name)

        return SourceFile(
            name=full_path.name,
            path=file_path,
            content=content,
            size=stat.st_size,
            modified=int(stat.st_mtime),
            created=int(stat.st_ctime),
            content_type=content_type,
        )

    def get_minimal_local_files(self, file_paths: list[str]) -> list[MinimalSourceFile]:
        """Get multiple files' metadata without content."""
        return [self._get_file_metadata(file_path=fp) for fp in file_paths]

    def _get_file_metadata(self, file_path: str) -> MinimalSourceFile:
        """Get metadata for a single file."""
        full_path = Path(self.base_path) / file_path

        stat = full_path.stat()

        return MinimalSourceFile(
            name=full_path.name,
            path=file_path,
            size=stat.st_size,
            modified=int(stat.st_mtime),
        )
