#!/usr/bin/env python3
"""
Source Discovery for Swiss AI-Hub Whitepaper

Uses LLM to automatically discover which documentation files are relevant
for each whitepaper chapter, eliminating manual maintenance of sources.txt files.

This solves the problem of sources.txt files drifting out of sync as
documentation grows and changes.

Usage:
  python generate-sources.py              # Update sources for all chapters
  python generate-sources.py 01 03 05     # Update specific chapters
  python generate-sources.py --list       # List available chapters
  python generate-sources.py --dry-run    # Preview without writing files
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from llm_utils import Colors, UsageTracker, call_llm


@dataclass
class DocInfo:
    """Information about a documentation file."""

    path: str  # Relative path from docs root (e.g., "2_platform/5_agents/index.en.md")
    title: str  # Extracted title from first heading
    summary: str  # First paragraph or description


@dataclass
class Config:
    """Configuration for source discovery."""

    script_dir: Path
    prompts_dir: Path
    sources_dir: Path
    docs_root: Path
    llm_model: str = "gemini-3-flash-preview"  # Use fast model for discovery


def extract_doc_info(file_path: Path, docs_root: Path) -> DocInfo | None:
    """Extract title and summary from a markdown documentation file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Get relative path
    rel_path = str(file_path.relative_to(docs_root))

    # Extract title from first # heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem

    # Extract summary - first non-empty paragraph after title
    # Skip frontmatter if present
    content_without_frontmatter = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)

    # Find first paragraph (non-heading, non-empty lines)
    paragraphs = re.split(r"\n\s*\n", content_without_frontmatter)
    summary = ""
    for para in paragraphs:
        para = para.strip()
        # Skip headings, empty lines, and very short content
        if para and not para.startswith("#") and len(para) > 20:
            # Take first 200 chars
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

        # Keep comment lines for organization
        if line.startswith("#"):
            lines.append(line)
            continue

        # Skip empty lines
        if not line:
            continue

        # Validate path exists in our documentation
        if line in valid_paths:
            lines.append(line)
        else:
            # Try common variations
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
    chapter_id: str,
    config: Config,
    doc_manifest: str,
    valid_paths: set[str],
    usage_tracker: UsageTracker,
) -> list[str] | None:
    """Discover relevant source files for a chapter using LLM."""
    prompt_file = config.prompts_dir / f"{chapter_id}_prompt.md"

    if not prompt_file.exists():
        print(Colors.red(f"✗ Prompt file not found: {prompt_file}"), file=sys.stderr)
        return None

    chapter_prompt = prompt_file.read_text()

    print(Colors.blue("  📝 Building discovery prompt..."))
    prompt = build_discovery_prompt(chapter_prompt, doc_manifest)

    print(Colors.blue(f"  🤖 Calling LLM ({config.llm_model})..."))
    success, output = call_llm(prompt, config.llm_model)

    # Track usage
    usage_tracker.track_last_call()

    if not success:
        print(Colors.red(f"  ✗ LLM call failed: {output[:200]}"), file=sys.stderr)
        return None

    print(Colors.blue("  🔍 Parsing and validating paths..."))
    sources = parse_llm_output(output, valid_paths)

    return sources


def write_sources_file(chapter_id: str, sources: list[str], config: Config) -> None:
    """Write sources to the sources file."""
    output_file = config.sources_dir / f"{chapter_id}_sources.txt"

    # Read chapter prompt to get title for header
    prompt_file = config.prompts_dir / f"{chapter_id}_prompt.md"
    chapter_title = f"Chapter {chapter_id}"
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


def get_all_chapter_ids(prompts_dir: Path) -> list[str]:
    """Get all available chapter IDs from prompts directory."""
    chapter_ids = []
    for prompt_file in sorted(prompts_dir.glob("*_prompt.md")):
        chapter_id = prompt_file.stem.replace("_prompt", "")
        chapter_ids.append(chapter_id)
    return chapter_ids


def list_chapters(config: Config) -> None:
    """List all available chapters."""
    print(Colors.blue("Available chapters:"))

    for prompt_file in sorted(config.prompts_dir.glob("*_prompt.md")):
        chapter_id = prompt_file.stem.replace("_prompt", "")
        sources_file = config.sources_dir / f"{chapter_id}_sources.txt"
        has_sources = "✓" if sources_file.exists() else " "

        # Count sources if file exists
        source_count = 0
        if sources_file.exists():
            for line in sources_file.read_text().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    source_count += 1

        print(f"  {chapter_id}: sources[{has_sources}] ({source_count} files)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM-based source discovery for whitepaper chapters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "chapters",
        nargs="*",
        help="Chapter IDs to update (e.g., 01 03 05). If not specified, updates all.",
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
    return Config(
        script_dir=script_dir,
        prompts_dir=script_dir / "prompts",
        sources_dir=script_dir / "sources",
        docs_root=script_dir.parent / "docs",
        llm_model=model,
    )


def validate_config(config: Config) -> bool:
    """Validate that required directories exist. Returns True if valid."""
    if not config.docs_root.exists():
        print(Colors.red(f"Error: Documentation root not found: {config.docs_root}"), file=sys.stderr)
        return False
    if not config.prompts_dir.exists():
        print(Colors.red(f"Error: Prompts directory not found: {config.prompts_dir}"), file=sys.stderr)
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
    print(Colors.green(f"Chapters to process: {', '.join(chapters)}"))
    print(Colors.blue(f"Model: {model}"))
    if dry_run:
        print(Colors.yellow("DRY RUN - no files will be written"))
    print()


def process_single_chapter(
    chapter_id: str,
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
    print(Colors.blue(f"Chapter {chapter_id} ({idx}/{total})"))
    print(Colors.blue("━" * 51))

    sources = discover_sources_for_chapter(chapter_id, config, doc_manifest, valid_paths, usage_tracker)

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
        config.sources_dir.mkdir(parents=True, exist_ok=True)
        write_sources_file(chapter_id, sources, config)
        output_file = config.sources_dir / f"{chapter_id}_sources.txt"
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

    chapters = args.chapters if args.chapters else get_all_chapter_ids(config.prompts_dir)
    if not chapters:
        print(Colors.yellow("No chapters found to process"))
        return 0

    print_header(chapters, config.llm_model, args.dry_run)

    usage_tracker = UsageTracker(model=config.llm_model)
    success_count = 0
    fail_count = 0

    for idx, chapter_id in enumerate(chapters, start=1):
        if process_single_chapter(
            chapter_id, idx, len(chapters), config, doc_manifest, valid_paths, usage_tracker, args.dry_run
        ):
            success_count += 1
        else:
            fail_count += 1

    print_summary(success_count, fail_count, usage_tracker)

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
