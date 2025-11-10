import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.LocalFile import LocalFile, MinimalLocalFile


@dataclass
class ScanConfig:
    """Compiled regex patterns for file scanning."""

    folder_patterns: list[re.Pattern] | None
    subfolder_patterns: list[re.Pattern] | None
    exclude_folder_patterns: list[re.Pattern]
    exclude_path_patterns: list[re.Pattern]
    extension_patterns: list[re.Pattern] | None
    exclude_file_patterns: list[re.Pattern]


class LocalFileSystemResource(ConfigurableResource):
    """
    Scans local file systems using regex patterns for flexible filtering.

    Tip: Use helper functions from aihub_pipeline.util.pattern_utils:
    - exact_match_pattern(["A", "B"]) -> '^(A|B)$'
    - extension_pattern([".pdf", ".docx"]) -> '\\.(pdf|docx)$'
    - contains_pattern("archive") -> '.*archive.*'
    """

    base_path: Annotated[str, Field(description="Base path to start scanning from")]

    target_folder_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Regex patterns for folders to scan. None = scan all folders recursively from base_path",
        ),
    ]

    target_subfolder_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Regex patterns for subfolders within matched folders. "
            "None = scan all subfolders recursively. "
            "Only applies when target_folder_patterns is specified.",
        ),
    ]

    exclude_folder_patterns: Annotated[
        list[str] | None,
        Field(
            default_factory=lambda: [r".*archiv.*"],
            description="Regex patterns to exclude folders (case-insensitive)",
        ),
    ]

    exclude_path_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Regex patterns to exclude by full relative path",
        ),
    ]

    file_extension_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Regex patterns for file extensions. None = all types",
        ),
    ]

    exclude_file_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Regex patterns for file names to exclude",
        ),
    ]

    _scan_config: ScanConfig | None = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        self._scan_config = self._compile_patterns()

    def _compile_patterns(self) -> ScanConfig:
        """Compile all regex patterns once during initialization."""

        def compile_list(patterns: list[str] | None) -> list[re.Pattern]:
            return [re.compile(p, re.IGNORECASE) for p in patterns] if patterns else []

        def compile_optional(patterns: list[str] | None) -> list[re.Pattern] | None:
            return [re.compile(p, re.IGNORECASE) for p in patterns] if patterns else None

        return ScanConfig(
            folder_patterns=compile_optional(self.target_folder_patterns),
            subfolder_patterns=compile_optional(self.target_subfolder_patterns),
            exclude_folder_patterns=compile_list(self.exclude_folder_patterns),
            exclude_path_patterns=compile_list(self.exclude_path_patterns),
            extension_patterns=compile_optional(self.file_extension_patterns),
            exclude_file_patterns=compile_list(self.exclude_file_patterns),
        )

    def fetch_all_files(self) -> list[MinimalLocalFile]:
        """Fetch all files matching configured patterns."""
        base = Path(self.base_path)

        if not base.exists():
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")

        if self._scan_config.folder_patterns is None:
            return self._scan_recursively(directory=base, source_folder="", subfolder=None)

        return self._scan_targeted_folders(base=base)

    def _scan_targeted_folders(self, base: Path) -> list[MinimalLocalFile]:
        """Scan specific folders matching patterns."""
        all_files = []

        for item in base.iterdir():
            if not item.is_dir():
                continue

            if not self._matches_any(text=item.name, patterns=self._scan_config.folder_patterns):
                continue

            if self._is_excluded_folder(folder_name=item.name):
                continue

            all_files.extend(self._process_folder(folder=item, folder_name=item.name))

        return all_files

    def _process_folder(self, folder: Path, folder_name: str) -> list[MinimalLocalFile]:
        """Process a folder based on subfolder patterns."""
        if self._scan_config.subfolder_patterns is None:
            return self._scan_recursively(directory=folder, source_folder=folder_name, subfolder=None)

        return self._scan_targeted_subfolders(folder=folder, folder_name=folder_name)

    def _scan_targeted_subfolders(self, folder: Path, folder_name: str) -> list[MinimalLocalFile]:
        """Scan specific subfolders within a folder."""
        all_files = []

        for subfolder in folder.iterdir():
            if not subfolder.is_dir():
                continue

            if not self._matches_any(text=subfolder.name, patterns=self._scan_config.subfolder_patterns):
                continue

            if self._is_excluded_folder(folder_name=subfolder.name):
                continue

            files = self._scan_recursively(directory=subfolder, source_folder=folder_name, subfolder=subfolder.name)
            all_files.extend(files)

        return all_files

    def _scan_recursively(self, directory: Path, source_folder: str, subfolder: str | None) -> list[MinimalLocalFile]:
        """Recursively scan directory for matching files."""
        files = []

        for item in directory.rglob("*"):
            if item.is_file():
                if file := self._process_file(file_path=item, source_folder=source_folder, subfolder=subfolder):
                    files.append(file)

        return files

    def _process_file(self, file_path: Path, source_folder: str, subfolder: str | None) -> MinimalLocalFile | None:
        """Process a single file if it passes all filters."""
        relative_path = file_path.relative_to(self.base_path).as_posix()

        if not self._should_include_file(file_path=file_path, relative_path=relative_path):
            return None

        stat = file_path.stat()
        return MinimalLocalFile(
            name=file_path.name,
            path=relative_path,
            size=stat.st_size,
            modified=int(stat.st_mtime),
            source_folder=source_folder,
            subfolder=subfolder,
        )

    def _should_include_file(self, file_path: Path, relative_path: str) -> bool:
        """Check if file passes all inclusion filters."""
        if self._matches_any(text=relative_path, patterns=self._scan_config.exclude_path_patterns):
            return False

        if self._has_excluded_parent(file_path=file_path):
            return False

        if self._matches_any(text=file_path.name, patterns=self._scan_config.exclude_file_patterns):
            return False

        if not self._matches_extension(filename=file_path.name):
            return False

        return True

    def _has_excluded_parent(self, file_path: Path) -> bool:
        """Check if any parent folder is excluded."""
        base = Path(self.base_path)
        for parent in file_path.parents:
            if parent == base:
                break
            if self._is_excluded_folder(folder_name=parent.name):
                return True
        return False

    def _is_excluded_folder(self, folder_name: str) -> bool:
        """Check if folder matches exclusion patterns."""
        return self._matches_any(text=folder_name, patterns=self._scan_config.exclude_folder_patterns)

    def _matches_extension(self, filename: str) -> bool:
        """Check if file extension matches patterns."""
        if self._scan_config.extension_patterns is None:
            return True
        return self._matches_any(text=filename, patterns=self._scan_config.extension_patterns)

    @staticmethod
    def _matches_any(text: str, patterns: list[re.Pattern] | None) -> bool:
        """Check if text matches any pattern in the list."""
        if patterns is None:
            return True
        if not patterns:
            return False
        return any(pattern.search(text) for pattern in patterns)

    def get_local_file(self, file_path: str) -> LocalFile:
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

        path_parts = Path(file_path).parts
        source_folder = path_parts[0] if path_parts else ""
        subfolder = path_parts[1] if len(path_parts) > 1 else None

        return LocalFile(
            name=full_path.name,
            path=file_path,
            content=content,
            size=stat.st_size,
            modified=int(stat.st_mtime),
            created=int(stat.st_ctime),
            content_type=content_type,
            source_folder=source_folder,
            subfolder=subfolder,
        )

    async def get_minimal_local_files(self, file_paths: list[str]) -> list[MinimalLocalFile]:
        """Get multiple files' metadata without content."""
        return [self._get_file_metadata(file_path=fp) for fp in file_paths]

    def _get_file_metadata(self, file_path: str) -> MinimalLocalFile:
        """Get metadata for a single file."""
        full_path = Path(self.base_path) / file_path

        stat = full_path.stat()
        path_parts = Path(file_path).parts

        return MinimalLocalFile(
            name=full_path.name,
            path=file_path,
            size=stat.st_size,
            modified=int(stat.st_mtime),
            source_folder=path_parts[0] if path_parts else "",
            subfolder=path_parts[1] if len(path_parts) > 1 else "",
        )
