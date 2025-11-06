import mimetypes
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from dagster import ConfigurableResource, get_dagster_logger
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.LocalFile import LocalFile, MinimalLocalFile


class LocalFileSystemResource(ConfigurableResource):
    base_path: Annotated[
        str,
        Field(description="Base path to the file system root (e.g., /mnt/smb_bmd/30 GP/31 Kunden)"),
    ]
    target_folders: Annotated[
        list[str],
        Field(description="List of folder names to process"),
    ]
    target_subfolders: Annotated[
        list[str],
        Field(description="Subfolders within each target folder to scan (e.g., '02 SNK Kran')"),
    ]
    exclude_folders: Annotated[
        list[str] | None,
        Field(
            default_factory=lambda: [r".*archiv.*"],
            description="List of regular expressions. "
            "Any folder whose name matches one of these patterns (case-insensitive) will be excluded.",
        ),
    ]
    supported_filetypes: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Optional list of regex patterns to filter files by extension. "
            "None (default) = allow ALL file types. "
            "Provide a list to restrict to specific types, e.g., [r'\\.pdf$', r'\\.docx?$']",
        ),
    ]

    _compiled_exclude_patterns: list[re.Pattern] | None = PrivateAttr(default=None)
    _compiled_include_patterns: list[re.Pattern] | None = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)

        if self.exclude_folders:
            self._compiled_exclude_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.exclude_folders]
        else:
            self._compiled_exclude_patterns = []

        if self.supported_filetypes is None:
            self._compiled_include_patterns = None
        else:
            self._compiled_include_patterns = [
                re.compile(pattern, re.IGNORECASE) for pattern in self.supported_filetypes
            ]


    def _is_file_included(self, filename: str) -> bool:
        if not self._compiled_include_patterns:
            return True

        _, extension = os.path.splitext(filename)
        if not extension:
            return False

        return any(pattern.search(extension.lower()) for pattern in self._compiled_include_patterns)

    @staticmethod
    def _extract_relative_path(parent_path: str, filename: str) -> str:
        if "/root:/" in parent_path:
            return parent_path.split("/root:/", 1)[1] + "/" + filename
        return filename

    def _is_folder_excluded(self, folder_name: str) -> bool:
        if not self._compiled_exclude_patterns:
            return False
        return any(pattern.match(folder_name) for pattern in self._compiled_exclude_patterns)

    def fetch_all_files(self) -> list[MinimalLocalFile]:
        """
        Fetch all files from configured customer folders and subfolders.
        """
        logger = get_dagster_logger()
        all_files = []

        base = Path(self.base_path)
        if not base.exists():
            logger.error(f"Base path does not exist: {self.base_path}")
            return all_files

        for customer_folder in self.target_folders:
            for subfolder in self.target_subfolders:
                customer_path = base / customer_folder / subfolder

                if not customer_path.exists():
                    logger.warning(f"Path does not exist: {customer_path}")
                    continue

                logger.info(f"Scanning: {customer_path}")

                try:
                    files = self._scan_directory_recursive(customer_path, customer_folder, subfolder)
                    all_files.extend(files)
                    logger.info(f"Found {len(files)} files in {customer_folder}/{subfolder}")
                except Exception as e:
                    logger.error(f"Error scanning {customer_path}: {e}")

        logger.info(f"Total files found: {len(all_files)}")
        return all_files

    def _scan_directory_recursive(self, directory: Path, customer_folder: str, subfolder: str) -> list[MinimalLocalFile]:
        """
        Recursively scan a directory for files.
        """
        logger = get_dagster_logger()
        files = []

        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    # Check if file should be excluded based on parent folder
                    if self._should_exclude_file(item):
                        continue

                    # Check if file type is supported
                    if not self._is_file_included(item.name):
                        continue

                    try:
                        stat = item.stat()
                        relative_path = item.relative_to(Path(self.base_path))

                        files.append(MinimalLocalFile(
                            name=item.name,
                            path=str(relative_path),
                            full_path=str(item),
                            size=stat.st_size,
                            modified=stat.st_mtime,
                            created=stat.st_ctime,
                            source_folder=customer_folder,
                            subfolder=subfolder,
                        ))
                    except Exception as e:
                        logger.warning(f"Error processing file {item}: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied accessing {directory}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return files

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded based on its parent folders."""
        if not self._compiled_exclude_patterns:
            return False

        for parent in file_path.parents:
            if any(pattern.search(parent.name) for pattern in self._compiled_exclude_patterns):
                return True
        return False

    def get_local_file(self, file_path: str) -> LocalFile:
        """
        Get a single file with its content by partition key (relative path).
        """
        logger = get_dagster_logger()
        full_path = Path(self.base_path) / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {full_path}")

        logger.info(f"Reading file: {full_path}")

        # Read file content
        with open(full_path, "rb") as f:
            content = f.read()

        # Get file stats
        stat = full_path.stat()

        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path.name)

        # Create ISO timestamp strings
        modified_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        created_iso = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()

        # Extract source_folder and subfolder from path
        path_parts = Path(file_path).parts
        source_folder = path_parts[0] if len(path_parts) > 0 else ""
        subfolder = path_parts[1] if len(path_parts) > 1 else None

        return LocalFile(
            name=full_path.name,
            path=file_path,
            content=content,
            size=stat.st_size,
            modified=modified_iso,
            created=created_iso,
            content_type=content_type,
            full_path=str(full_path),
            source_folder=source_folder,
            subfolder=subfolder,
        )

    async def get_minimal_local_files(self, file_paths: list[str]) -> list[MinimalLocalFile]:
        """
        Get multiple files' metadata (without content) by partition keys.
        """
        logger = get_dagster_logger()
        files = []

        for file_path in file_paths:
            try:
                full_path = Path(self.base_path) / file_path

                if not full_path.exists() or not full_path.is_file():
                    logger.warning(f"Skipping invalid path: {full_path}")
                    continue

                stat = full_path.stat()

                # Extract source_folder and subfolder from path
                path_parts = Path(file_path).parts
                source_folder = path_parts[0] if len(path_parts) > 0 else ""
                subfolder = path_parts[1] if len(path_parts) > 1 else ""

                files.append(MinimalLocalFile(
                    name=full_path.name,
                    path=file_path,
                    full_path=str(full_path),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    created=stat.st_ctime,
                    source_folder=source_folder,
                    subfolder=subfolder,
                ))
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

        logger.info(f"Retrieved metadata for {len(files)} files")
        return files