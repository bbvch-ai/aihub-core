#!/usr/bin/env python3
"""
Whitepaper Chapter Combiner
Combines all generated whitepaper chapters from the output directory into a single document.

Reads all XX_output.md files (00_output.md, 01_output.md, etc.) in numerical order
and combines them into a single markdown file, optionally converting to DOCX.
"""

import os
import re
from pathlib import Path


def extract_chapter_number(filename):
    """
    Extract chapter number from filename for sorting.

    Examples:
        '00_output.md' -> 0
        '01_output.md' -> 1
        '10_output.md' -> 10
        'other.md' -> float('inf') (non-chapter files sort last)

    Args:
        filename: Name of the file

    Returns:
        Chapter number as integer, or infinity if not a chapter file
    """
    match = re.match(r"^(\d+)_output\.md$", filename)
    if match:
        return int(match.group(1))
    return float('inf')


def read_chapter_file(file_path):
    """
    Read a chapter markdown file.

    Args:
        file_path: Path to the chapter file

    Returns:
        Content of the file as string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"⚠️  Warning: Could not read {file_path}: {e}")
        return ""


def get_chapter_title(content):
    """
    Extract chapter title from the first H1 heading.

    Args:
        content: Markdown content

    Returns:
        Title string or None if no H1 found
    """
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def combine_chapters(output_dir, add_page_breaks=True):
    """
    Combine all chapter files from output directory.

    Args:
        output_dir: Directory containing XX_output.md files
        add_page_breaks: Whether to add page breaks between chapters

    Returns:
        Combined markdown content as string
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"✗ Error: Directory '{output_dir}' does not exist")
        return ""

    # Get all chapter files and sort by chapter number
    chapter_files = []
    for file in output_path.iterdir():
        if file.is_file() and file.name.endswith("_output.md"):
            chapter_files.append(file)

    chapter_files.sort(key=lambda f: extract_chapter_number(f.name))

    if not chapter_files:
        print(f"✗ Error: No chapter files found in {output_dir}")
        return ""

    print(f"Found {len(chapter_files)} chapter file(s):\n")

    # Combine all chapters
    sections = []

    for chapter_file in chapter_files:
        chapter_num = extract_chapter_number(chapter_file.name)
        content = read_chapter_file(chapter_file)

        if content:
            # Get chapter title for logging
            title = get_chapter_title(content)
            if title:
                print(f"  ✓ Chapter {chapter_num:02d}: {title}")
            else:
                print(f"  ✓ Chapter {chapter_num:02d}: {chapter_file.name}")

            # Add content
            sections.append(content.strip())

            # Add page break between chapters (for DOCX conversion)
            if add_page_breaks and chapter_file != chapter_files[-1]:
                sections.append("\n\n\\newpage\n\n")
            else:
                sections.append("\n\n")

    print()
    return "".join(sections)


def save_markdown(content, output_path):
    """
    Save combined markdown content to file.

    Args:
        content: Markdown content
        output_path: Path where to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"✓ Created {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error saving markdown: {e}")
        return False


def convert_to_docx(markdown_path, docx_path):
    """
    Convert markdown file to DOCX using pypandoc.

    Args:
        markdown_path: Path to input markdown file
        docx_path: Path to output DOCX file

    Returns:
        True if successful, False otherwise
    """
    try:
        import pypandoc

        # Convert with page breaks support
        pypandoc.convert_file(
            markdown_path,
            "docx",
            outputfile=docx_path,
            extra_args=["--standalone"]
        )
        print(f"✓ Created {docx_path}")
        return True
    except ImportError:
        print("\n⚠️  pypandoc not installed (DOCX conversion skipped)")
        print("   Install with: pip install pypandoc")
        print("   Also install pandoc: https://pandoc.org/installing.html")
        return False
    except Exception as e:
        print(f"✗ Error converting to DOCX: {e}")
        return False


def create_table_of_contents(chapters_dir):
    """
    Create a table of contents from chapter files.

    Args:
        chapters_dir: Directory containing chapter files

    Returns:
        Table of contents as markdown string
    """
    output_path = Path(chapters_dir)
    chapter_files = []

    for file in output_path.iterdir():
        if file.is_file() and file.name.endswith("_output.md"):
            chapter_files.append(file)

    chapter_files.sort(key=lambda f: extract_chapter_number(f.name))

    toc = ["# Inhaltsverzeichnis\n"]

    for chapter_file in chapter_files:
        chapter_num = extract_chapter_number(chapter_file.name)
        content = read_chapter_file(chapter_file)

        if content:
            title = get_chapter_title(content)
            if title:
                toc.append(f"{chapter_num}. {title}\n")

    toc.append("\n\\newpage\n\n")
    return "".join(toc)


def merge_whitepaper(chapters_dir="./output", output_name="whitepaper", include_toc=True):
    """
    Main function to merge whitepaper chapters and create DOCX.

    Args:
        chapters_dir: Directory containing chapter files (default: ./output)
        output_name: Base name for output files without extension (default: whitepaper)
        include_toc: Whether to include table of contents (default: True)
    """
    print("╔══════════════════════════════════════════════════╗")
    print("║       Swiss AI-Hub Whitepaper Combiner          ║")
    print("╚══════════════════════════════════════════════════╝\n")

    chapters_path = Path(chapters_dir).resolve()
    print(f"Processing chapters from: {chapters_path}\n")

    # Create table of contents
    toc_content = ""
    if include_toc:
        print("Creating table of contents...\n")
        toc_content = create_table_of_contents(chapters_path)

    # Combine all chapters
    combined_content = combine_chapters(chapters_path, add_page_breaks=True)

    if not combined_content.strip():
        print("✗ No content to combine")
        return

    # Add TOC at the beginning
    if toc_content:
        combined_content = toc_content + combined_content

    # Save combined markdown
    markdown_output = f"{output_name}.md"
    if not save_markdown(combined_content, markdown_output):
        return

    # Convert to DOCX
    docx_output = f"{output_name}.docx"
    convert_to_docx(markdown_output, docx_output)

    # Calculate stats
    word_count = len(combined_content.split())
    page_estimate = word_count / 400  # ~400 words per page

    print("\n" + "═" * 50)
    print("Statistics:")
    print(f"  Total word count: {word_count:,}")
    print(f"  Estimated pages: {page_estimate:.1f}")
    print("═" * 50)

    print("\n✓ Done!")


if __name__ == "__main__":
    import sys

    # Configuration
    CHAPTERS_DIR = "./output"
    OUTPUT_FILENAME = "swiss_ai_hub_whitepaper"
    INCLUDE_TOC = True

    # Parse command line arguments
    if len(sys.argv) > 1:
        CHAPTERS_DIR = sys.argv[1]
    if len(sys.argv) > 2:
        OUTPUT_FILENAME = sys.argv[2]
    if len(sys.argv) > 3:
        INCLUDE_TOC = sys.argv[3].lower() in ("true", "1", "yes")

    # Run the merger
    merge_whitepaper(CHAPTERS_DIR, OUTPUT_FILENAME, INCLUDE_TOC)
