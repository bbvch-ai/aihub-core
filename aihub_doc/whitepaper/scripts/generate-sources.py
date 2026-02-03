#!/usr/bin/env python3
"""
Source Discovery for Swiss AI-Hub Whitepaper

Uses LLM to automatically discover which documentation files are relevant
for each whitepaper chapter, eliminating manual maintenance of sources.md files.

This solves the problem of sources.md files drifting out of sync as
documentation grows and changes.

Usage:
  python generate-sources.py                        # Update sources for all chapters
  python generate-sources.py 00-executive-summary   # Update specific chapter
  python generate-sources.py --list                 # List available chapters
  python generate-sources.py --dry-run              # Preview without writing files
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from llm_utils import Colors, UsageTracker, call_llm

# File name constants
PROMPT_FILE = "prompt.md"
SOURCES_FILE = "sources.md"


@dataclass
class DocInfo:
    """Information about a documentation file."""

    path: str  # Relative path from docs root (e.g., "2_platform/5_agents/index.en.md")
    title: str  # Extracted title from first heading
    summary: str  # First paragraph or description


@dataclass
class Config:
    """Configuration for source discovery."""

    whitepaper_dir: Path
    chapters_dir: Path
    docs_root: Path
    llm_model: str = "gemini-3-flash-preview"  # Use fast model for discovery


def extract_doc_info(file_path: Path, docs_root: Path) -> DocInfo | None:
    """Extract title and summary from a markdown documentation file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    rel_path = str(file_path.relative_to(docs_root))

    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem

    content_without_frontmatter = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)

    paragraphs = re.split(r"\n\s*\n", content_without_frontmatter)
    summary = ""
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith("#") and len(para) > 20:
            summary = para[:200].replace("\n", " ")
            break

    return DocInfo(path=rel_path, title=title, summary=summary)


def scan_documentation(docs_root: Path) -> list[DocInfo]:
    """Scan all documentation files and extract metadata."""
    docs = []

    for md_file in sorted(docs_root.rglob("*.en.md")):
        doc_info = extract_doc_info(md_file, docs_root)
        if doc_info:
            docs.append(doc_info)

    return docs


def build_doc_manifest(docs: list[DocInfo]) -> str:
    """Build a text manifest of all available documentation."""
    lines = ["# Available Documentation Files", ""]

    for doc in docs:
        lines.append(f"## {doc.path}")
        lines.append(f"Title: {doc.title}")
        if doc.summary:
            lines.append(f"Summary: {doc.summary}...")
        lines.append("")

    return "\n".join(lines)


def build_discovery_prompt(chapter_prompt: str, doc_manifest: str) -> str:
    """Build the prompt for LLM source discovery."""
    return f"""You are a documentation analyst. Your task is to identify which documentation files are relevant for a specific whitepaper chapter.

## Chapter Requirements

{chapter_prompt}

## Available Documentation

{doc_manifest}

## Instructions

Based on the chapter requirements above, identify ALL documentation files that contain information relevant to this chapter.

**Output Format:**
- Output ONLY the file paths, one per line
- Use the exact paths as shown in "Available Documentation" (e.g., "2_platform/5_agents/index.en.md")
- Group related files together with a comment line starting with #
- Do NOT include any other text or explanation

**Selection Criteria:**
- Include files that directly address the chapter's key topics
- Include files that provide supporting context or technical details
- Include files about features, architecture, or concepts mentioned in the chapter objectives
- Prefer comprehensive/index files over very narrow sub-topics
- When in doubt, include the file - it's better to have extra context than miss important information

**Example Output Format:**
# Main topic area
2_platform/5_agents/index.en.md
2_platform/5_agents/1_overview/index.en.md

# Supporting documentation
2_platform/2_architecture/index.en.md
"""


def parse_llm_output(output: str, valid_paths: set[str]) -> list[str]:
    """Parse LLM output and extract valid file paths."""
    lines = []

    for line in output.strip().split("\n"):
        line = line.strip()

        if line.startswith("#"):
            lines.append(line)
            continue

        if not line:
            continue

        if line in valid_paths:
            lines.append(line)
        else:
            variations = [
                line,
                line.replace(".de.md", ".en.md"),
                line.replace(".md", ".en.md"),
            ]
            for var in variations:
                if var in valid_paths:
                    lines.append(var)
                    break

    return lines


def discover_sources_for_chapter(
    chapter_name: str,
    config: Config,
    doc_manifest: str,
    valid_paths: set[str],
    usage_tracker: UsageTracker,
) -> list[str] | None:
    """Discover relevant source files for a chapter using LLM."""
    chapter_dir = config.chapters_dir / chapter_name
    prompt_file = chapter_dir / PROMPT_FILE

    if not prompt_file.exists():
        print(Colors.red(f"✗ Prompt file not found: {prompt_file}"), file=sys.stderr)
        return None

    chapter_prompt = prompt_file.read_text()

    print(Colors.blue("  📝 Building discovery prompt..."))
    prompt = build_discovery_prompt(chapter_prompt, doc_manifest)

    print(Colors.blue(f"  🤖 Calling LLM ({config.llm_model})..."))
    success, output = call_llm(prompt, config.llm_model)

    usage_tracker.track_last_call()

    if not success:
        print(Colors.red(f"  ✗ LLM call failed: {output[:200]}"), file=sys.stderr)
        return None

    print(Colors.blue("  🔍 Parsing and validating paths..."))
    sources = parse_llm_output(output, valid_paths)

    return sources


def write_sources_file(chapter_name: str, sources: list[str], config: Config) -> None:
    """Write sources to the sources file."""
    chapter_dir = config.chapters_dir / chapter_name
    output_file = chapter_dir / SOURCES_FILE

    prompt_file = chapter_dir / PROMPT_FILE
    chapter_title = chapter_name
    if prompt_file.exists():
        first_line = prompt_file.read_text().split("\n")[0]
        if first_line.startswith("#"):
            chapter_title = first_line.lstrip("#").strip()

    lines = [
        f"# Source Documentation for {chapter_title}",
        "# Auto-generated by generate-sources.py - can be manually adjusted",
        "# Paths relative to aihub_doc/docs/",
        "",
    ]
    lines.extend(sources)
    lines.append("")  # Trailing newline

    output_file.write_text("\n".join(lines))


def get_all_chapter_names(chapters_dir: Path) -> list[str]:
    """Get all available chapter names from chapters directory."""
    chapter_names = []
    for chapter_dir in sorted(chapters_dir.iterdir()):
        if chapter_dir.is_dir() and (chapter_dir / PROMPT_FILE).exists():
            chapter_names.append(chapter_dir.name)
    return chapter_names


def resolve_chapter_name(chapter_input: str, chapters_dir: Path) -> str | None:
    """
    Resolve a chapter input to the full chapter name.

    Supports:
    - Full name: "01-business-challenge" -> "01-business-challenge"
    - Numeric prefix: "01" -> "01-business-challenge"
    - Partial match: "business" -> "01-business-challenge" (if unique)

    Returns None if no match or ambiguous.
    """
    all_chapters = get_all_chapter_names(chapters_dir)

    # Exact match
    if chapter_input in all_chapters:
        return chapter_input

    # Prefix match (e.g., "01" matches "01-business-challenge")
    prefix_matches = [c for c in all_chapters if c.startswith(chapter_input + "-") or c == chapter_input]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    # Numeric prefix match (e.g., "1" matches "01-...")
    try:
        num = int(chapter_input)
        num_prefix = f"{num:02d}-"
        num_matches = [c for c in all_chapters if c.startswith(num_prefix)]
        if len(num_matches) == 1:
            return num_matches[0]
    except ValueError:
        pass

    # Substring match (if unique)
    substring_matches = [c for c in all_chapters if chapter_input in c]
    if len(substring_matches) == 1:
        return substring_matches[0]

    return None


def list_chapters(config: Config) -> None:
    """List all available chapters."""
    print(Colors.blue("Available chapters:"))

    for chapter_dir in sorted(config.chapters_dir.iterdir()):
        if not chapter_dir.is_dir():
            continue

        chapter_name = chapter_dir.name
        sources_file = chapter_dir / SOURCES_FILE
        has_sources = "✓" if sources_file.exists() else " "

        source_count = 0
        if sources_file.exists():
            for line in sources_file.read_text().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    source_count += 1

        print(f"  {chapter_name}: sources[{has_sources}] ({source_count} files)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM-based source discovery for whitepaper chapters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "chapters",
        nargs="*",
        help="Chapter names to update (e.g., 00-executive-summary). If not specified, updates all.",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available chapters and exit",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview discovered sources without writing files",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=os.environ.get("LLM_MODEL", "gemini-3-flash-preview"),
        help="LLM model to use (default: gemini-3-flash-preview)",
    )
    return parser.parse_args()


def create_config(model: str) -> Config:
    """Create configuration from script location."""
    script_dir = Path(__file__).parent.resolve()
    whitepaper_dir = script_dir.parent
    return Config(
        whitepaper_dir=whitepaper_dir,
        chapters_dir=whitepaper_dir / "chapters",
        docs_root=whitepaper_dir.parent / "docs",
        llm_model=model,
    )


def validate_config(config: Config) -> bool:
    """Validate that required directories exist. Returns True if valid."""
    if not config.docs_root.exists():
        print(Colors.red(f"Error: Documentation root not found: {config.docs_root}"), file=sys.stderr)
        return False
    if not config.chapters_dir.exists():
        print(Colors.red(f"Error: Chapters directory not found: {config.chapters_dir}"), file=sys.stderr)
        return False
    return True


def prepare_documentation(config: Config) -> tuple[str, set[str]]:
    """Scan documentation and build manifest. Returns (manifest, valid_paths)."""
    print(Colors.blue("📚 Scanning documentation..."))
    docs = scan_documentation(config.docs_root)
    print(Colors.green(f"  ✓ Found {len(docs)} documentation files"))

    print(Colors.blue("📋 Building documentation manifest..."))
    doc_manifest = build_doc_manifest(docs)
    valid_paths = {doc.path for doc in docs}
    print(Colors.green(f"  ✓ Manifest ready ({len(doc_manifest)} chars)"))

    return doc_manifest, valid_paths


def print_header(chapters: list[str], model: str, dry_run: bool) -> None:
    """Print the application header."""
    print()
    print(Colors.blue("╔══════════════════════════════════════════════════╗"))
    print(Colors.blue("║       Source Discovery for Whitepaper           ║"))
    print(Colors.blue("╚══════════════════════════════════════════════════╝"))
    print()
    print(Colors.green(f"Chapters to process: {len(chapters)}"))
    print(Colors.blue(f"Model: {model}"))
    if dry_run:
        print(Colors.yellow("DRY RUN - no files will be written"))
    print()


def process_single_chapter(
    chapter_name: str,
    idx: int,
    total: int,
    config: Config,
    doc_manifest: str,
    valid_paths: set[str],
    usage_tracker: UsageTracker,
    dry_run: bool,
) -> bool:
    """Process a single chapter. Returns True on success."""
    print(Colors.blue("━" * 51))
    print(Colors.blue(f"Chapter {chapter_name} ({idx}/{total})"))
    print(Colors.blue("━" * 51))

    sources = discover_sources_for_chapter(chapter_name, config, doc_manifest, valid_paths, usage_tracker)

    if sources is None:
        print(Colors.red("  ✗ Failed to discover sources"))
        return False

    file_count = sum(1 for s in sources if not s.startswith("#"))
    print(Colors.green(f"  ✓ Discovered {file_count} relevant source files"))

    if dry_run:
        print(Colors.yellow("  Preview:"))
        for source in sources[:10]:
            print(Colors.yellow(f"    {source}"))
        if len(sources) > 10:
            print(Colors.yellow(f"    ... and {len(sources) - 10} more"))
    else:
        write_sources_file(chapter_name, sources, config)
        output_file = config.chapters_dir / chapter_name / SOURCES_FILE
        print(Colors.green(f"  ✓ Written to {output_file}"))

    print()
    return True


def print_summary(success_count: int, fail_count: int, usage_tracker: UsageTracker) -> None:
    """Print the final summary."""
    print(Colors.blue("═" * 51))
    print(Colors.green("Summary"))
    print(Colors.blue("═" * 51))
    print(Colors.green(f"✓ Successful: {success_count}"))
    if fail_count > 0:
        print(Colors.red(f"✗ Failed: {fail_count}"))
    print(usage_tracker.format_summary())


def resolve_chapters_from_args(chapter_inputs: list[str], chapters_dir: Path) -> list[str] | None:
    """Resolve chapter inputs to full chapter names. Returns None on error."""
    chapters = []
    for chapter_input in chapter_inputs:
        resolved = resolve_chapter_name(chapter_input, chapters_dir)
        if resolved:
            chapters.append(resolved)
        else:
            print(Colors.red(f"Error: Could not resolve chapter '{chapter_input}'"), file=sys.stderr)
            print(Colors.yellow("  Use --list to see available chapters"), file=sys.stderr)
            return None
    return chapters


def run_source_discovery(
    chapters: list[str], config: Config, doc_manifest: str, valid_paths: set[str], dry_run: bool
) -> int:
    """Run source discovery for chapters. Returns exit code."""
    usage_tracker = UsageTracker(model=config.llm_model)
    success_count = 0
    fail_count = 0

    for idx, chapter_name in enumerate(chapters, start=1):
        if process_single_chapter(chapter_name, idx, len(chapters), config, doc_manifest, valid_paths, usage_tracker, dry_run):
            success_count += 1
        else:
            fail_count += 1

    print_summary(success_count, fail_count, usage_tracker)
    return 1 if fail_count > 0 else 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    config = create_config(args.model)

    if not validate_config(config):
        return 1

    if args.list:
        list_chapters(config)
        return 0

    doc_manifest, valid_paths = prepare_documentation(config)

    if args.chapters:
        chapters = resolve_chapters_from_args(args.chapters, config.chapters_dir)
        if chapters is None:
            return 1
    else:
        chapters = get_all_chapter_names(config.chapters_dir)

    if not chapters:
        print(Colors.yellow("No chapters found to process"))
        return 0

    print_header(chapters, config.llm_model, args.dry_run)
    return run_source_discovery(chapters, config, doc_manifest, valid_paths, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
