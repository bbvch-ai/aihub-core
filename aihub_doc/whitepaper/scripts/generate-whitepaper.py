#!/usr/bin/env python3
"""
Whitepaper Generator for Swiss AI-Hub

Generates business-focused whitepaper chapters using LLM with Jinja2 templates.
Each chapter is self-contained in its own directory with prompt, sources, and output.

Features:
  - Generates new chapters from technical documentation
  - Intelligently improves existing chapters when regenerating
  - Preserves manual adjustments while integrating new information
  - Maintains consistency across all chapters
  - Uses Jinja2 templates for clean prompt construction

Usage: python generate-whitepaper.py [chapter_name...]
  If no chapter_name provided, generates all chapters
  Example: python generate-whitepaper.py 00-executive-summary 03-data-sovereignty
"""

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from llm_utils import Colors, UsageTracker, call_llm

# File name constants
PROMPT_FILE = "prompt.md"
SOURCES_FILE = "sources.md"
OUTPUT_FILE = "output.md"


@dataclass
class SourceDocument:
    """Represents a source documentation file."""

    path: str
    content: str


@dataclass
class Chapter:
    """Represents a generated chapter."""

    name: str
    content: str


@dataclass
class GeneratorConfig:
    """Configuration for the whitepaper generator."""

    whitepaper_dir: Path
    chapters_dir: Path
    templates_dir: Path
    config_dir: Path
    docs_root: Path
    project_root: Path
    llm_model: str = "gemini-3-flash-preview"
    max_retries: int = 3
    retry_delay: int = 5
    lang_suffix: str = ".de.md"

    @property
    def general_prompt_file(self) -> Path:
        return self.config_dir / "general_prompt.md"

    @property
    def glossary_file(self) -> Path:
        return self.config_dir / "glossary.md"


class WhitepaperGenerator:
    """Main generator class for creating whitepaper chapters."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the generator with configuration."""
        self.config = config
        self.usage_tracker = UsageTracker(model=config.llm_model)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.config.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _get_chapter_dir(self, chapter_name: str) -> Path:
        """Get the directory path for a chapter."""
        return self.config.chapters_dir / chapter_name

    def _get_chapter_number(self, chapter_name: str) -> int:
        """Extract the numeric prefix from a chapter name (e.g., '03-data-sovereignty' -> 3)."""
        try:
            return int(chapter_name.split("-")[0])
        except (ValueError, IndexError):
            return -1

    def check_requirements(self) -> None:
        """Check that all required tools and files exist."""
        if not self._command_exists("llm"):
            print(
                Colors.red("Error: 'llm' command not found. Please install using 'pipx install llm'"),
                file=sys.stderr,
            )
            print("See: https://github.com/simonw/llm", file=sys.stderr)
            sys.exit(1)

        checks = [
            (self.config.general_prompt_file, "General prompt file"),
            (self.config.chapters_dir, "Chapters directory"),
            (self.config.docs_root, "Documentation root"),
        ]

        for path, name in checks:
            if not path.exists():
                print(Colors.red(f"Error: {name} not found: {path}"), file=sys.stderr)
                sys.exit(1)

        if not self.config.glossary_file.exists():
            print(Colors.yellow(f"ℹ️  Glossary file not found: {self.config.glossary_file}"))
            print(Colors.yellow("   Continuing without terminology glossary"))

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                ["which", command],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _mdformat_available(self) -> bool:
        """Check if mdformat is available."""
        return self._command_exists("mdformat")

    def format_output_files(self) -> bool:
        """
        Format all output markdown files in chapter directories using mdformat.
        Uses the project's pyproject.toml configuration if available.

        Returns:
            True if formatting succeeded, False otherwise
        """
        if not self._mdformat_available():
            print(Colors.yellow("ℹ️  mdformat not available, skipping formatting"))
            print(Colors.yellow("   Install with: pip install mdformat"))
            return False

        # Find all output.md files in chapter directories
        md_files = [f.resolve() for f in self.config.chapters_dir.glob(f"*/{OUTPUT_FILE}")]

        if not md_files:
            print(Colors.yellow("ℹ️  No output markdown files found"))
            return False

        print()
        print(Colors.blue("🎨 Formatting output markdown files with mdformat..."))
        print(Colors.blue(f"   Found {len(md_files)} file(s) to format"))

        pyproject_toml = self.config.project_root / "pyproject.toml"
        if pyproject_toml.exists():
            print(Colors.blue(f"   Using config from: {pyproject_toml}"))
        else:
            print(Colors.yellow(f"   Warning: pyproject.toml not found at {pyproject_toml}"))

        try:
            cmd = ["mdformat"] + [str(f) for f in md_files]
            print(Colors.blue(f"   Running from: {self.config.project_root}"))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.config.project_root),
            )

            if result.returncode == 0:
                print(Colors.green(f"✓ Successfully formatted {len(md_files)} markdown file(s)"))
                if result.stdout:
                    print(Colors.blue(f"   {result.stdout}"))
                return True
            else:
                print(Colors.red(f"✗ mdformat failed with exit code {result.returncode}"), file=sys.stderr)
                if result.stderr:
                    print(Colors.yellow(f"   stderr: {result.stderr}"), file=sys.stderr)
                if result.stdout:
                    print(Colors.yellow(f"   stdout: {result.stdout}"), file=sys.stderr)
                return False
        except subprocess.TimeoutExpired:
            print(Colors.yellow("⚠️  mdformat timed out"), file=sys.stderr)
            return False
        except Exception as e:
            print(Colors.yellow(f"⚠️  mdformat error: {e}"), file=sys.stderr)
            return False

    def get_source_files(self, chapter_name: str) -> list[str]:
        """Read source file list for a chapter."""
        source_file = self._get_chapter_dir(chapter_name) / SOURCES_FILE

        if not source_file.exists():
            print(
                Colors.yellow(f"Warning: No source file found for chapter {chapter_name}: {source_file}"),
                file=sys.stderr,
            )
            return []

        lines = []
        for line in source_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)

        return lines

    def load_source_documents(self, chapter_name: str) -> list[SourceDocument]:
        """Load source documents for a chapter."""
        source_files = self.get_source_files(chapter_name)
        documents = []

        for doc_path in source_files:
            doc_path = doc_path.strip()
            de_doc_path = doc_path.replace(".en.md", self.config.lang_suffix)
            full_path = self.config.docs_root / de_doc_path

            if full_path.exists():
                documents.append(
                    SourceDocument(
                        path=de_doc_path,
                        content=full_path.read_text(),
                    )
                )
            else:
                full_path = self.config.docs_root / doc_path
                if full_path.exists():
                    documents.append(
                        SourceDocument(
                            path=doc_path,
                            content=full_path.read_text(),
                        )
                    )

        return documents

    def load_previous_chapters(self, chapter_name: str) -> list[Chapter]:
        """Load all previously generated chapters for context."""
        current_num = self._get_chapter_number(chapter_name)
        if current_num < 0:
            print(Colors.yellow(f"Warning: Invalid chapter name format: {chapter_name}"), file=sys.stderr)
            return []

        chapters = []
        all_chapters = self.get_all_chapter_names()

        for prev_chapter in all_chapters:
            prev_num = self._get_chapter_number(prev_chapter)
            if 0 <= prev_num < current_num:
                output_file = self._get_chapter_dir(prev_chapter) / OUTPUT_FILE
                if output_file.exists():
                    chapters.append(
                        Chapter(
                            name=prev_chapter,
                            content=output_file.read_text(),
                        )
                    )

        return chapters

    def build_prompt(self, chapter_name: str) -> str:
        """Build combined prompt using Jinja2 template."""
        template = self.env.get_template("full_prompt.j2")
        chapter_dir = self._get_chapter_dir(chapter_name)

        chapter_prompt_file = chapter_dir / PROMPT_FILE
        if not chapter_prompt_file.exists():
            raise FileNotFoundError(f"Chapter prompt not found: {chapter_prompt_file}")

        chapter_prompt = chapter_prompt_file.read_text()
        general_prompt = self.config.general_prompt_file.read_text()
        glossary = self.config.glossary_file.read_text() if self.config.glossary_file.exists() else ""
        source_documents = self.load_source_documents(chapter_name)
        previous_chapters = self.load_previous_chapters(chapter_name)

        output_file = chapter_dir / OUTPUT_FILE
        existing_chapter = output_file.read_text() if output_file.exists() else None

        return template.render(
            chapter_id=chapter_name,
            chapter_prompt=chapter_prompt,
            general_prompt=general_prompt,
            glossary=glossary,
            source_documents=source_documents,
            previous_chapters=previous_chapters,
            existing_chapter=existing_chapter,
        )

    def _print_chapter_header(self, chapter_name: str, output_file: Path, prompt_file: Path) -> None:
        """Print chapter generation header."""
        print(Colors.blue("═" * 51))
        if output_file.exists():
            print(Colors.green(f"Improving Existing Chapter: {chapter_name}"))
        else:
            print(Colors.green(f"Generating New Chapter: {chapter_name}"))
        print(Colors.blue("═" * 51))

        print(Colors.blue(f"📝 Using prompt: {prompt_file}"))
        print(Colors.blue(f"🤖 Using model: {self.config.llm_model}"))
        print(Colors.blue(f"📂 DOCS_ROOT: {self.config.docs_root}"))

        if output_file.exists():
            print(Colors.yellow("📄 Existing chapter found - will improve with new documentation"))

    def _collect_and_show_sources(self, chapter_name: str) -> int:
        """Collect and display source documents. Returns file count."""
        print(Colors.blue("📚 Collecting source documentation..."))
        source_files = self.get_source_files(chapter_name)
        file_count = 0

        for doc_path in source_files:
            doc_path = doc_path.strip()
            de_doc_path = doc_path.replace(".en.md", self.config.lang_suffix)
            full_path = self.config.docs_root / de_doc_path

            if full_path.exists():
                print(Colors.blue(f"  📄 {de_doc_path}"))
                file_count += 1
            elif (self.config.docs_root / doc_path).exists():
                print(Colors.blue(f"  📄 {doc_path}"))
                file_count += 1
            else:
                print(Colors.yellow(f"  ⚠️  Not found: {doc_path}"), file=sys.stderr)

        print(Colors.green(f"  ✓ Collected {file_count} source document(s)"))
        return file_count

    def _show_previous_chapters(self, chapter_name: str) -> None:
        """Show information about previous chapters."""
        print(Colors.blue("📖 Checking for previous chapters..."))
        previous_chapters = self.load_previous_chapters(chapter_name)

        if not previous_chapters:
            print(Colors.blue("  ℹ️  No previous chapters (this is the first chapter)"))
        else:
            for chapter in previous_chapters:
                print(Colors.blue(f"  📗 Chapter {chapter.name} (for context)"))
            print(Colors.green(f"  ✓ Including {len(previous_chapters)} previous chapter(s) for consistency"))

    def _call_llm_with_retry(self, prompt: str, output_file: Path) -> bool:
        """Call LLM with retry logic. Returns True on success."""
        for attempt in range(1, self.config.max_retries + 1):
            print(Colors.blue(f"🔄 Attempt {attempt}/{self.config.max_retries}: Calling LLM..."))

            success, output = call_llm(prompt, self.config.llm_model)
            self.usage_tracker.track_last_call()

            if success:
                output_file.write_text(output)
                word_count = len(output.split())
                print(Colors.green("✓ Chapter generated successfully"))
                print(Colors.green(f"  📄 Output: {output_file}"))
                print(Colors.green(f"  📊 Word count: {word_count}"))
                return True

            print(Colors.yellow(f"⚠️  LLM call failed on attempt {attempt}"), file=sys.stderr)
            if output:
                print(Colors.yellow(f"     Error output: {output[:300]}"), file=sys.stderr)

            if attempt < self.config.max_retries:
                print(Colors.yellow(f"⏳ Waiting {self.config.retry_delay}s before retry..."))
                time.sleep(self.config.retry_delay)

        return False

    def generate_chapter(self, chapter_name: str) -> bool:
        """Generate a single chapter using LLM."""
        chapter_dir = self._get_chapter_dir(chapter_name)
        output_file = chapter_dir / OUTPUT_FILE
        prompt_file = chapter_dir / PROMPT_FILE

        if not prompt_file.exists():
            print(Colors.red(f"✗ Prompt file not found: {prompt_file}"), file=sys.stderr)
            return False

        self._print_chapter_header(chapter_name, output_file, prompt_file)
        self._collect_and_show_sources(chapter_name)
        self._show_previous_chapters(chapter_name)

        print(Colors.blue("🔨 Building combined prompt..."))
        try:
            prompt = self.build_prompt(chapter_name)
        except Exception as e:
            print(Colors.red(f"✗ Failed to build prompt: {e}"), file=sys.stderr)
            return False

        prompt_size = len(prompt.encode("utf-8"))
        print(Colors.blue(f"  📊 Combined prompt size: {self._format_bytes(prompt_size)}"))

        if not self._call_llm_with_retry(prompt, output_file):
            print(
                Colors.red(f"✗ Failed to generate chapter {chapter_name} after {self.config.max_retries} attempts"),
                file=sys.stderr,
            )
            return False

        return True

    def list_chapters(self) -> None:
        """List all available chapters."""
        print(Colors.blue("Available chapters:"))

        for chapter_dir in sorted(self.config.chapters_dir.iterdir()):
            if not chapter_dir.is_dir():
                continue

            chapter_name = chapter_dir.name
            has_prompt = "✓" if (chapter_dir / PROMPT_FILE).exists() else "✗"
            has_sources = "✓" if (chapter_dir / SOURCES_FILE).exists() else "✗"
            has_output = "✓" if (chapter_dir / OUTPUT_FILE).exists() else " "

            print(f"  {chapter_name}: prompt[{has_prompt}] sources[{has_sources}] output[{has_output}]")

    def get_all_chapter_names(self) -> list[str]:
        """Get all available chapter names from chapters directory."""
        chapter_names = []
        for chapter_dir in sorted(self.config.chapters_dir.iterdir()):
            if chapter_dir.is_dir() and (chapter_dir / PROMPT_FILE).exists():
                chapter_names.append(chapter_dir.name)
        return chapter_names

    def resolve_chapter_name(self, chapter_input: str) -> str | None:
        """
        Resolve a chapter input to the full chapter name.

        Supports:
        - Full name: "01-business-challenge" -> "01-business-challenge"
        - Numeric prefix: "01" -> "01-business-challenge"
        - Partial match: "business" -> "01-business-challenge" (if unique)

        Returns None if no match or ambiguous.
        """
        all_chapters = self.get_all_chapter_names()

        # Exact match
        if chapter_input in all_chapters:
            return chapter_input

        # Prefix match (e.g., "01" matches "01-business-challenge")
        prefix_matches = [c for c in all_chapters if c.startswith(chapter_input + "-") or c == chapter_input]
        if len(prefix_matches) == 1:
            return prefix_matches[0]

        # Numeric prefix match (e.g., "1" matches "01-...")
        if chapter_input.isdigit():
            num = int(chapter_input)
            num_prefix = f"{num:02d}-"
            num_matches = [c for c in all_chapters if c.startswith(num_prefix)]
            if len(num_matches) == 1:
                return num_matches[0]

        # Substring match (if unique)
        substring_matches = [c for c in all_chapters if chapter_input in c]
        if len(substring_matches) == 1:
            return substring_matches[0]

        return None

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format byte size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"


def print_header(chapters_count: int, model: str) -> None:
    """Print the application header."""
    print()
    print(Colors.blue("╔══════════════════════════════════════════════════╗"))
    print(Colors.blue("║       Swiss AI-Hub Whitepaper Generator         ║"))
    print(Colors.blue("╚══════════════════════════════════════════════════╝"))
    print()
    print(Colors.green(f"Total chapters to generate: {chapters_count}"))
    print(Colors.blue(f"Model: {model}"))
    print()


def print_summary(success_count: int, fail_count: int, failed_chapters: list[str]) -> None:
    """Print the generation summary."""
    print(Colors.blue("═" * 51))
    print(Colors.green("Generation Summary"))
    print(Colors.blue("═" * 51))
    print(Colors.green(f"✓ Successful: {success_count}"))
    if fail_count > 0:
        print(Colors.red(f"✗ Failed: {fail_count}"))
    if failed_chapters:
        print(Colors.red(f"Failed chapters: {' '.join(failed_chapters)}"))


def run_generation(generator: WhitepaperGenerator, chapters: list[str]) -> list[str]:
    """Run chapter generation. Returns list of failed chapters."""
    failed_chapters = []

    for idx, chapter_name in enumerate(chapters, start=1):
        print(Colors.blue("━" * 51))
        print(Colors.blue(f"Processing chapter {chapter_name} ({idx}/{len(chapters)})"))
        print(Colors.blue("━" * 51))
        print()

        if generator.generate_chapter(chapter_name):
            print(Colors.green(f"✓ Chapter {chapter_name} completed successfully"))
        else:
            failed_chapters.append(chapter_name)
            print(Colors.red(f"✗ Chapter {chapter_name} failed"))

        print()
        print(Colors.blue(f"Progress: ✓ {idx - len(failed_chapters)} successful, ✗ {len(failed_chapters)} failed"))
        print()

    return failed_chapters


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Swiss AI-Hub Whitepaper Generator",
        epilog="""
Examples:
  %(prog)s                              # Generate all chapters
  %(prog)s 00-executive-summary         # Generate by full name
  %(prog)s 01 03                        # Generate by number prefix
  %(prog)s business sovereignty         # Generate by keyword (if unique)
  LLM_MODEL=gpt-4 %(prog)s              # Use different model
  %(prog)s --list                       # List available chapters
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "chapters",
        nargs="*",
        help="Chapter names to generate (e.g., 00-executive-summary). If not specified, generates all chapters.",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available chapters and exit",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=os.environ.get("LLM_MODEL", "gemini-3-flash-preview"),
        help="LLM model to use (default: gemini-3-flash-preview, or LLM_MODEL env var)",
    )

    args = parser.parse_args()

    # Setup configuration - scripts/ is inside whitepaper/
    script_dir = Path(__file__).parent.resolve()
    whitepaper_dir = script_dir.parent
    project_root = whitepaper_dir.parent.parent  # whitepaper -> aihub_doc -> aihub-core

    config = GeneratorConfig(
        whitepaper_dir=whitepaper_dir,
        chapters_dir=whitepaper_dir / "chapters",
        templates_dir=whitepaper_dir / "templates",
        config_dir=whitepaper_dir / "config",
        docs_root=whitepaper_dir.parent / "docs",
        project_root=project_root,
        llm_model=args.model,
    )

    generator = WhitepaperGenerator(config)
    generator.check_requirements()

    if args.list:
        generator.list_chapters()
        return 0

    chapters_to_generate = _resolve_chapters(args.chapters, generator)
    if chapters_to_generate is None:
        return 1

    if not chapters_to_generate:
        print(Colors.yellow("No chapters found to generate"))
        generator.list_chapters()
        return 0

    print_header(len(chapters_to_generate), config.llm_model)
    failed_chapters = run_generation(generator, chapters_to_generate)

    print_summary(len(chapters_to_generate) - len(failed_chapters), len(failed_chapters), failed_chapters)

    if not failed_chapters:
        generator.format_output_files()

    print(generator.usage_tracker.format_summary())
    print()

    if not failed_chapters:
        print(Colors.green("✓ All chapters generated successfully!"))
    print(Colors.blue(f"Chapters directory: {config.chapters_dir}"))

    return 1 if failed_chapters else 0


def _resolve_chapters(chapter_args: list[str], generator: WhitepaperGenerator) -> list[str] | None:
    """Resolve chapter arguments to full names. Returns None on error."""
    if not chapter_args:
        print(Colors.green("No chapters specified, generating all available chapters"))
        return generator.get_all_chapter_names()

    chapters = []
    for chapter_input in chapter_args:
        resolved = generator.resolve_chapter_name(chapter_input)
        if resolved:
            chapters.append(resolved)
        else:
            print(Colors.red(f"Error: Could not resolve chapter '{chapter_input}'"), file=sys.stderr)
            print(Colors.yellow("  Use --list to see available chapters"), file=sys.stderr)
            return None

    print(Colors.green(f"Generating specified chapters: {' '.join(chapters)}"))
    return chapters


if __name__ == "__main__":
    sys.exit(main())
