"""
Markdown Documentation Merger
Combines German markdown files (index.de.md) from a directory structure into a single document
with proper heading hierarchy, then converts to DOCX.

The script processes directories in sorted order (by folder numbering) and always places
the index.de.md of the current directory first, before processing subdirectories.
"""

import os
import re
from pathlib import Path


def extract_numeric_prefix(name):
    """
    Extract the numeric prefix from a folder/file name for sorting.

    Examples:
        '1_vision' -> 1
        '10_chat_ui' -> 10
        'readme.md' -> float('inf') (items without numbers sort last)

    Args:
        name: Folder or file name

    Returns:
        Numeric prefix as integer, or infinity if no prefix found
    """
    match = re.match(r"^(\d+)", name)
    if match:
        return int(match.group(1))
    return float("inf")


def clean_folder_name(folder_name):
    """
    Convert folder name to readable title.
    Examples:
        '1_vision_and_positioning' -> 'Vision And Positioning'
        '2_context' -> 'Context'
    """
    # Remove leading numbers and underscores (e.g., '1_', '2_')
    clean_name = re.sub(r"^\d+_", "", folder_name)
    # Replace underscores with spaces
    clean_name = clean_name.replace("_", " ")
    # Capitalize each word
    return clean_name.title()


def adjust_markdown_headings(content, heading_offset):
    """
    Increase heading levels in markdown content.
    Example: If offset=2, '# Title' becomes '### Title'

    Args:
        content: Original markdown content
        heading_offset: Number of levels to increase headings by

    Returns:
        Modified markdown with adjusted heading levels
    """

    def increase_heading_level(match):
        current_hashes = match.group(1)
        heading_text = match.group(2)

        new_level = len(current_hashes) + heading_offset
        # Markdown supports max 6 heading levels
        new_level = min(new_level, 6)

        return "#" * new_level + heading_text

    # Find all markdown headings (lines starting with # symbols)
    pattern = r"^(#{1,6})(.+)$"
    return re.sub(pattern, increase_heading_level, content, flags=re.MULTILINE)


def fix_image_paths(content, source_file_path, root_path):
    """
    Convert relative image paths to be relative to the root directory.

    Args:
        content: Markdown content
        source_file_path: Path to the original markdown file
        root_path: Root directory path

    Returns:
        Content with fixed image paths
    """
    source_dir = os.path.dirname(os.path.abspath(source_file_path))
    root_path = os.path.abspath(root_path)

    def replace_image_path(match):
        alt_text = match.group(1)
        image_path = match.group(2)

        # Skip if already absolute path or URL
        if image_path.startswith(("http://", "https://", "/", "\\")):
            return match.group(0)

        # Resolve the absolute path of the image
        absolute_image_path = os.path.abspath(os.path.join(source_dir, image_path))

        # Calculate path relative to root directory
        try:
            # Get the relative path from root to the image
            relative_to_root = os.path.relpath(absolute_image_path, start=root_path)

            # Convert backslashes to forward slashes
            relative_to_root = relative_to_root.replace("\\", "/")

            # Ensure it starts with ./
            if not relative_to_root.startswith("./"):
                relative_to_root = "./" + relative_to_root

            return f"![{alt_text}]({relative_to_root})"
        except ValueError:
            # If path is on different drive (Windows), keep original
            return match.group(0)

    # Match markdown image syntax: ![alt](path)
    pattern = r"!\[(.*?)\]\((.*?)\)"
    return re.sub(pattern, replace_image_path, content)


def convert_custom_blocks(content):
    """
    Convert custom markdown blocks (like ::: tip, ::: warning) to Word-compatible format.

    Converts blocks like:
        ::: tip Title
        Content here
        :::

    To:
        **💡 Title**

        Content here
    """
    # Define block types and their emoji/formatting
    block_types = {
        "tip": "💡",
        "info": "ℹ️",
        "warning": "⚠️",
        "danger": "🚨",
        "note": "📝",
        "important": "❗",
        "caution": "⚡",
        "detail": "🔍",
    }

    def replace_block(match):
        block_type = match.group(1).lower()
        title_and_content = match.group(2).strip()

        # Split first line (title) from rest (content)
        lines = title_and_content.split("\n", 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        # Get emoji for block type, default to 📌 if unknown
        emoji = block_types.get(block_type, "📌")

        # Format as bold title with emoji, then content in blockquote
        result = f"**{emoji} {title}**\n\n"
        if content:
            # Add content as indented blockquote
            content_lines = content.split("\n")
            quoted_content = "\n".join(f"> {line}" for line in content_lines)
            result += f"{quoted_content}\n\n"

        return result

    # Match ::: blocks with any type
    # Pattern: ::: type_name, content (possibly multi-line), closing :::
    pattern = r":::\s*(\w+)\s+(.*?)\s*:::"
    return re.sub(pattern, replace_block, content, flags=re.DOTALL)


def strip_yaml_frontmatter(content):
    """
    Remove ALL YAML frontmatter blocks from markdown content.

    YAML frontmatter is enclosed by --- markers:
    ---
    key: value
    ---

    This function removes all such blocks, whether at the start or middle of the file.

    Args:
        content: Markdown content that may contain YAML frontmatter

    Returns:
        Content with all YAML frontmatter removed
    """
    # Pattern to match YAML frontmatter anywhere in the file
    # Matches: ---, any content, ---, with optional surrounding whitespace
    # The (?:^|\n) ensures we match at line boundaries
    pattern = r"(?:^|\n)---\s*\n.*?\n---\s*(?:\n|$)"
    return re.sub(pattern, "\n\n", content, flags=re.DOTALL)


def read_markdown_file(file_path, root_path):
    """
    Read markdown file and fix image paths.

    Args:
        file_path: Path to markdown file
        root_path: Root directory for relative path calculations
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            # Strip YAML frontmatter
            content = strip_yaml_frontmatter(content)
            # Fix image paths
            content = fix_image_paths(content, file_path, root_path)
            # Convert custom blocks to Word-compatible format
            content = convert_custom_blocks(content)
            return content
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return ""


def process_directory(root_path, current_path, output_dir, depth=0):
    """
    Recursively process directory and combine all German markdown files (index.de.md).

    Args:
        root_path: The starting directory path
        current_path: Current directory being processed
        output_dir: Directory where output file will be created
        depth: Current depth in folder hierarchy (for heading levels)

    Returns:
        Combined markdown content as string
    """
    sections = []

    # Get list of items in current directory with NUMERICAL sorting by folder prefix
    try:
        items = sorted(os.listdir(current_path), key=extract_numeric_prefix)
    except PermissionError:
        print(f"Warning: Cannot access {current_path}")
        return ""

    # FIRST: Process index.de.md in the current directory (if it exists)
    index_file = os.path.join(current_path, "index.de.md")
    if os.path.isfile(index_file):
        content = read_markdown_file(index_file, output_dir)
        if content:
            # Adjust heading levels based on folder depth
            adjusted_content = adjust_markdown_headings(content, depth)
            sections.append(adjusted_content)
            sections.append("\n\n")  # Add spacing between files

    # SECOND: Process subdirectories in numerically sorted order
    for item in items:
        item_path = os.path.join(current_path, item)

        # Only process subdirectories (ignore files - we already handled index.de.md)
        if os.path.isdir(item_path):
            folder_title = clean_folder_name(item)
            heading_level = "#" * (depth + 1)
            sections.append(f"{heading_level} {folder_title}\n\n")

            # Process contents of subdirectory
            subdir_content = process_directory(root_path, item_path, output_dir, depth + 1)
            sections.append(subdir_content)

    return "".join(sections)


def save_markdown(content, output_path):
    """Save combined markdown content to file."""
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"✓ Created {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error saving markdown: {e}")
        return False


def convert_to_docx(markdown_path, docx_path):
    """Convert markdown file to DOCX using pypandoc."""
    try:
        import pypandoc

        pypandoc.convert_file(markdown_path, "docx", outputfile=docx_path)
        print(f"✓ Created {docx_path}")
        return True
    except ImportError:
        print("\n⚠ pypandoc not installed.")
        print("Install with: pip install pypandoc")
        print("Also install pandoc: https://pandoc.org/installing.html")
        return False
    except Exception as e:
        print(f"✗ Error converting to DOCX: {e}")
        return False


def merge_documentation(source_dir, output_name="combined"):
    """
    Main function to merge markdown files and create DOCX.

    Args:
        source_dir: Root directory containing markdown files
        output_name: Base name for output files (without extension)
    """
    source_path = Path(source_dir).resolve()

    # Validate source directory
    if not source_path.exists():
        print(f"✗ Error: Directory '{source_dir}' does not exist")
        return

    if not source_path.is_dir():
        print(f"✗ Error: '{source_dir}' is not a directory")
        return

    print(f"Processing directory: {source_path}\n")

    # Get current working directory (where output will be created)
    output_dir = Path.cwd()

    # Combine all markdown files
    # Pass output_dir instead of source_path for relative path calculation
    combined_content = process_directory(str(source_path), str(source_path), str(output_dir), depth=0)

    if not combined_content.strip():
        print("✗ No markdown content found")
        return

    # Save combined markdown
    markdown_output = f"{output_name}.md"
    if not save_markdown(combined_content, markdown_output):
        return

    # Convert to DOCX
    docx_output = f"{output_name}.docx"
    convert_to_docx(markdown_output, docx_output)

    print("\n✓ Done!")


if __name__ == "__main__":
    # Configuration
    SOURCE_DIRECTORY = "./docs/2_platform"
    OUTPUT_FILENAME = "platform_combined"

    # Run the merger
    merge_documentation(SOURCE_DIRECTORY, OUTPUT_FILENAME)
