#!/usr/bin/env python3
"""
Whitepaper Generator for Swiss AI-Hub

Generates business-focused whitepaper chapters using LLM with Jinja2 templates.
Each chapter has its own prompt and source document mapping.

Features:
  - Generates new chapters from technical documentation
  - Intelligently improves existing chapters when regenerating
  - Preserves manual adjustments while integrating new information
  - Maintains consistency across all chapters
  - Uses Jinja2 templates for clean prompt construction

Usage: python generate-whitepaper.py [chapter_id...]
  If no chapter_id provided, generates all chapters
  Example: python generate-whitepaper.py 01 03 05
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, Template


# --- ANSI Color Codes ---
class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color

    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.NC}"

    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.NC}"

    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.NC}"

    @classmethod
    def blue(cls, text: str) -> str:
        return f"{cls.BLUE}{text}{cls.NC}"


@dataclass
class SourceDocument:
    """Represents a source documentation file."""

    path: str
    content: str


@dataclass
class Chapter:
    """Represents a generated chapter."""

    id: str
    content: str


@dataclass
class GeneratorConfig:
    """Configuration for the whitepaper generator."""

    script_dir: Path
    templates_dir: Path
    prompts_dir: Path
    sources_dir: Path
    output_dir: Path
    docs_root: Path
    general_prompt_file: Path
    glossary_file: Path
    project_root: Path  # Root of the aihub-core project
    llm_model: str = "gemini-3-pro-preview"
    max_retries: int = 3
    retry_delay: int = 5
    lang_suffix: str = ".de.md"


class WhitepaperGenerator:
    """Main generator class for creating whitepaper chapters."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the generator with configuration."""
        self.config = config

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.config.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def check_requirements(self) -> None:
        """Check that all required tools and files exist."""
        # Check for llm command
        if not self._command_exists("llm"):
            print(
                Colors.red("Error: 'llm' command not found. Please install using 'pipx install llm'"),
                file=sys.stderr,
            )
            print("See: https://github.com/simonw/llm", file=sys.stderr)
            sys.exit(1)

        # Check for required directories and files
        checks = [
            (self.config.general_prompt_file, "General prompt file"),
            (self.config.prompts_dir, "Prompts directory"),
            (self.config.sources_dir, "Sources directory"),
            (self.config.docs_root, "Documentation root"),
        ]

        for path, name in checks:
            if not path.exists():
                print(Colors.red(f"Error: {name} not found: {path}"), file=sys.stderr)
                sys.exit(1)

        # Check for optional glossary file (warn if not found)
        if not self.config.glossary_file.exists():
            print(Colors.yellow(f"ℹ️  Glossary file not found: {self.config.glossary_file}"))
            print(Colors.yellow("   Continuing without terminology glossary"))

        # Create output directory if needed
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

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

    def format_output_directory(self) -> bool:
        """
        Format all markdown files in the output directory using mdformat.
        Uses the project's pyproject.toml configuration if available.

        Returns:
            True if formatting succeeded, False otherwise
        """
        if not self._mdformat_available():
            print(Colors.yellow("ℹ️  mdformat not available, skipping formatting"))
            print(Colors.yellow("   Install with: pip install mdformat"))
            return False

        # Find all .md files in output directory (ensure absolute paths)
        md_files = [f.resolve() for f in self.config.output_dir.glob("*.md")]

        if not md_files:
            print(Colors.yellow("ℹ️  No markdown files found in output directory"))
            return False

        print()
        print(Colors.blue("🎨 Formatting output markdown files with mdformat..."))
        print(Colors.blue(f"   Found {len(md_files)} file(s) to format"))

        # Check for project pyproject.toml
        pyproject_toml = self.config.project_root / "pyproject.toml"
        if pyproject_toml.exists():
            print(Colors.blue(f"   Using config from: {pyproject_toml}"))
        else:
            print(Colors.yellow(f"   Warning: pyproject.toml not found at {pyproject_toml}"))

        try:
            # Build mdformat command with absolute file paths
            cmd = ["mdformat"] + [str(f) for f in md_files]

            # Debug output
            print(Colors.blue(f"   Running from: {self.config.project_root}"))

            # Run from project root so mdformat can find pyproject.toml
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.config.project_root),  # Run from project root
            )

            if result.returncode == 0:
                print(Colors.green(f"✓ Successfully formatted {len(md_files)} markdown file(s)"))
                # Show stdout if there's any useful info
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

    def get_source_files(self, chapter_id: str) -> list[str]:
        """Read source file list for a chapter."""
        source_file = self.config.sources_dir / f"{chapter_id}_sources.txt"

        if not source_file.exists():
            print(
                Colors.yellow(f"Warning: No source file found for chapter {chapter_id}: {source_file}"), file=sys.stderr
            )
            return []

        # Read source file, skip comments and empty lines
        lines = []
        for line in source_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)

        return lines

    def load_source_documents(self, chapter_id: str) -> list[SourceDocument]:
        """Load source documents for a chapter."""
        source_files = self.get_source_files(chapter_id)
        documents = []

        for doc_path in source_files:
            # Strip whitespace and handle different line endings
            doc_path = doc_path.strip()

            # Convert to German documentation path if it has .en.md suffix
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
                # Fallback: try original path if German version doesn't exist
                full_path = self.config.docs_root / doc_path
                if full_path.exists():
                    documents.append(
                        SourceDocument(
                            path=doc_path,
                            content=full_path.read_text(),
                        )
                    )

        return documents

    def load_previous_chapters(self, chapter_id: str) -> list[Chapter]:
        """Load all previously generated chapters."""
        try:
            current_num = int(chapter_id)
        except ValueError:
            print(Colors.yellow(f"Warning: Invalid chapter ID format: {chapter_id}"), file=sys.stderr)
            return []

        chapters = []

        for i in range(current_num):
            prev_id = f"{i:02d}"
            output_file = self.config.output_dir / f"{prev_id}_output.md"

            if output_file.exists():
                chapters.append(
                    Chapter(
                        id=prev_id,
                        content=output_file.read_text(),
                    )
                )

        return chapters

    def build_prompt(self, chapter_id: str) -> str:
        """Build combined prompt using Jinja2 template."""
        template = self.env.get_template("full_prompt.j2")

        # Load all components
        chapter_prompt_file = self.config.prompts_dir / f"{chapter_id}_prompt.md"
        if not chapter_prompt_file.exists():
            raise FileNotFoundError(f"Chapter prompt not found: {chapter_prompt_file}")

        chapter_prompt = chapter_prompt_file.read_text()
        general_prompt = self.config.general_prompt_file.read_text()
        glossary = self.config.glossary_file.read_text() if self.config.glossary_file.exists() else ""
        source_documents = self.load_source_documents(chapter_id)
        previous_chapters = self.load_previous_chapters(chapter_id)

        output_file = self.config.output_dir / f"{chapter_id}_output.md"
        existing_chapter = output_file.read_text() if output_file.exists() else None

        # Render template
        return template.render(
            chapter_id=chapter_id,
            chapter_prompt=chapter_prompt,
            general_prompt=general_prompt,
            glossary=glossary,
            source_documents=source_documents,
            previous_chapters=previous_chapters,
            existing_chapter=existing_chapter,
        )

    def call_llm(self, prompt: str, model: str) -> tuple[bool, str]:
        """
        Call LLM with the given prompt.

        Returns:
            Tuple of (success: bool, output: str)
        """
        # Use temp file to avoid shell argument length limits
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            tmp.write(prompt)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["llm", "--no-stream", "-m", model],
                stdin=open(tmp_path, "r"),
                capture_output=True,
                text=True,
            )

            return (result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def generate_chapter(self, chapter_id: str) -> bool:
        """Generate a single chapter using LLM."""
        output_file = self.config.output_dir / f"{chapter_id}_output.md"
        prompt_file = self.config.prompts_dir / f"{chapter_id}_prompt.md"

        # Print header
        print(Colors.blue("═" * 51))
        if output_file.exists():
            print(Colors.green(f"Improving Existing Chapter: {chapter_id}"))
        else:
            print(Colors.green(f"Generating New Chapter: {chapter_id}"))
        print(Colors.blue("═" * 51))

        if not prompt_file.exists():
            print(Colors.red(f"✗ Prompt file not found: {prompt_file}"), file=sys.stderr)
            return False

        print(Colors.blue(f"📝 Using prompt: {prompt_file}"))
        print(Colors.blue(f"🤖 Using model: {self.config.llm_model}"))
        print(Colors.blue(f"📂 DOCS_ROOT: {self.config.docs_root}"))

        if output_file.exists():
            print(Colors.yellow("📄 Existing chapter found - will improve with new documentation"))

        # Collect and show source documents
        print(Colors.blue("📚 Collecting source documentation..."))
        source_files = self.get_source_files(chapter_id)
        file_count = 0

        for doc_path in source_files:
            doc_path = doc_path.strip()
            de_doc_path = doc_path.replace(".en.md", self.config.lang_suffix)
            full_path = self.config.docs_root / de_doc_path

            if full_path.exists():
                print(Colors.blue(f"  📄 {de_doc_path}"))
                file_count += 1
            else:
                full_path = self.config.docs_root / doc_path
                if full_path.exists():
                    print(Colors.blue(f"  📄 {doc_path}"))
                    file_count += 1
                else:
                    print(Colors.yellow(f"  ⚠️  Not found: {doc_path}"), file=sys.stderr)
                    print(Colors.yellow(f"      (Looking for: {full_path})"), file=sys.stderr)

        print(Colors.green(f"  ✓ Collected {file_count} source document(s)"))

        # Check and show previous chapters
        print(Colors.blue("📖 Checking for previous chapters..."))
        previous_chapters = self.load_previous_chapters(chapter_id)

        if not previous_chapters:
            print(Colors.blue("  ℹ️  No previous chapters (this is the first chapter)"))
        else:
            for chapter in previous_chapters:
                print(Colors.blue(f"  📗 Chapter {chapter.id} (for context)"))
            print(Colors.green(f"  ✓ Including {len(previous_chapters)} previous chapter(s) for consistency"))

        # Build prompt
        print(Colors.blue("🔨 Building combined prompt..."))
        try:
            prompt = self.build_prompt(chapter_id)
        except Exception as e:
            print(Colors.red(f"✗ Failed to build prompt: {e}"), file=sys.stderr)
            return False

        prompt_size = len(prompt.encode("utf-8"))
        print(Colors.blue(f"  📊 Combined prompt size: {self._format_bytes(prompt_size)}"))

        # Generate with retry logic
        for attempt in range(1, self.config.max_retries + 1):
            print(Colors.blue(f"🔄 Attempt {attempt}/{self.config.max_retries}: Calling LLM..."))

            success, output = self.call_llm(prompt, self.config.llm_model)

            if success:
                # Write output
                output_file.write_text(output)

                word_count = len(output.split())
                print(Colors.green("✓ Chapter generated successfully"))
                print(Colors.green(f"  📄 Output: {output_file}"))
                print(Colors.green(f"  📊 Word count: {word_count}"))
                return True
            else:
                print(Colors.yellow(f"⚠️  LLM call failed on attempt {attempt}"), file=sys.stderr)
                if output:
                    print(Colors.yellow(f"     Error output: {output[:300]}"), file=sys.stderr)

                if attempt < self.config.max_retries:
                    print(Colors.yellow(f"⏳ Waiting {self.config.retry_delay}s before retry..."))
                    time.sleep(self.config.retry_delay)

        print(
            Colors.red(f"✗ Failed to generate chapter {chapter_id} after {self.config.max_retries} attempts"),
            file=sys.stderr,
        )
        return False

    def list_chapters(self) -> None:
        """List all available chapters."""
        print(Colors.blue("Available chapters:"))

        for prompt_file in sorted(self.config.prompts_dir.glob("*_prompt.md")):
            chapter_id = prompt_file.stem.replace("_prompt", "")
            has_sources = "✓" if (self.config.sources_dir / f"{chapter_id}_sources.txt").exists() else "✗"
            has_output = "✓" if (self.config.output_dir / f"{chapter_id}_output.md").exists() else " "

            print(f"  {chapter_id}: sources[{has_sources}] output[{has_output}]")

    def get_all_chapter_ids(self) -> list[str]:
        """Get all available chapter IDs from prompts directory."""
        chapter_ids = []
        for prompt_file in sorted(self.config.prompts_dir.glob("*_prompt.md")):
            chapter_id = prompt_file.stem.replace("_prompt", "")
            chapter_ids.append(chapter_id)
        return chapter_ids

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format byte size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Swiss AI-Hub Whitepaper Generator",
        epilog="""
Examples:
  %(prog)s                     # Generate all chapters
  %(prog)s 01 03 05            # Generate chapters 01, 03, and 05
  LLM_MODEL=gpt-4 %(prog)s     # Use different model
  %(prog)s --list              # List available chapters
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "chapters",
        nargs="*",
        help="Chapter IDs to generate (e.g., 01 03 05). If not specified, generates all chapters.",
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
        default=os.environ.get("LLM_MODEL", "gemini-3-pro-preview"),
        help="LLM model to use (default: gemini-3-pro-preview, or LLM_MODEL env var)",
    )

    args = parser.parse_args()

    # Setup configuration
    script_dir = Path(__file__).parent.resolve()  # Ensure absolute path
    project_root = script_dir.parent.parent  # aihub_doc/whitepaper -> aihub_doc -> aihub-core
    config = GeneratorConfig(
        script_dir=script_dir,
        templates_dir=script_dir / "templates",
        prompts_dir=script_dir / "prompts",
        sources_dir=script_dir / "sources",
        output_dir=script_dir / "output",
        docs_root=script_dir.parent / "docs",
        general_prompt_file=script_dir / "general_prompt.md",
        glossary_file=script_dir / "glossary.md",
        project_root=project_root,
        llm_model=args.model,
    )

    generator = WhitepaperGenerator(config)
    generator.check_requirements()

    # Handle --list flag
    if args.list:
        generator.list_chapters()
        return 0

    # Determine which chapters to generate
    if args.chapters:
        chapters_to_generate = args.chapters
        print(Colors.green(f"Generating specified chapters: {' '.join(chapters_to_generate)}"))
    else:
        chapters_to_generate = generator.get_all_chapter_ids()
        print(Colors.green("No chapters specified, generating all available chapters"))

    if not chapters_to_generate:
        print(Colors.yellow("No chapters found to generate"))
        generator.list_chapters()
        return 0

    # Print header
    print()
    print(Colors.blue("╔══════════════════════════════════════════════════╗"))
    print(Colors.blue("║       Swiss AI-Hub Whitepaper Generator         ║"))
    print(Colors.blue("╚══════════════════════════════════════════════════╝"))
    print()
    print(Colors.green(f"Total chapters to generate: {len(chapters_to_generate)}"))
    print(Colors.blue(f"Model: {config.llm_model}"))
    print()

    # Generate chapters
    success_count = 0
    fail_count = 0
    failed_chapters = []

    for idx, chapter_id in enumerate(chapters_to_generate, start=1):
        print(Colors.blue("━" * 51))
        print(Colors.blue(f"Processing chapter {chapter_id} ({idx}/{len(chapters_to_generate)})"))
        print(Colors.blue("━" * 51))
        print()

        if generator.generate_chapter(chapter_id):
            success_count += 1
            print(Colors.green(f"✓ Chapter {chapter_id} completed successfully"))
        else:
            fail_count += 1
            failed_chapters.append(chapter_id)
            print(Colors.red(f"✗ Chapter {chapter_id} failed"))

        print()
        print(Colors.blue(f"Progress: ✓ {success_count} successful, ✗ {fail_count} failed"))
        print()

    # Print summary
    print(Colors.blue("═" * 51))
    print(Colors.green("Generation Summary"))
    print(Colors.blue("═" * 51))
    print(Colors.green(f"✓ Successful: {success_count}"))
    if fail_count > 0:
        print(Colors.red(f"✗ Failed: {fail_count}"))

    if failed_chapters:
        print(Colors.red(f"Failed chapters: {' '.join(failed_chapters)}"))
        # Don't format if there were failures
    else:
        # Format all output files if all chapters succeeded
        generator.format_output_directory()

    print()
    if not failed_chapters:
        print(Colors.green("✓ All chapters generated successfully!"))
    print(Colors.blue(f"Output directory: {config.output_dir}"))

    return 1 if failed_chapters else 0


if __name__ == "__main__":
    sys.exit(main())
