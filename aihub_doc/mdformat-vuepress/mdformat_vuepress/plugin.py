# mdformat_vuepress/plugin.py
import re
from typing import List, Dict, Any

# --- container detection ---
START_RE = re.compile(r"^[ \t]*:::[^\n]*$")
END_RE = re.compile(r"^[ \t]*:::\s*$")

# Global storage for VuePress containers during processing
_CONTAINER_INFO = []


def _extract_containers_for_formatting(text: str) -> str:
    """Extract VuePress containers, preserve markers but allow content formatting."""
    global _CONTAINER_INFO
    _CONTAINER_INFO = []

    lines = text.splitlines(keepends=True)
    i, n = 0, len(lines)
    out = []

    while i < n:
        line = lines[i]
        if START_RE.match(line.rstrip("\n")):
            # Found start of container
            start_line = line.rstrip("\n")
            start_pos = i
            i += 1

            # Collect content lines
            content_lines = []
            while i < n and not END_RE.match(lines[i].rstrip("\n")):
                content_lines.append(lines[i])
                i += 1

            if i >= n:
                # No matching end found, treat as regular content
                out.extend(lines[start_pos:])
                break

            # Found matching end
            end_line = lines[i].rstrip("\n")

            # Store container info for later restoration
            container_id = len(_CONTAINER_INFO)
            _CONTAINER_INFO.append(
                {
                    "id": container_id,
                    "start": start_line,
                    "end": end_line,
                }
            )

            # Add content to be formatted, with special markers
            out.append(f"<!--VUEPRESS_START_{container_id}-->\n")
            out.extend(content_lines)
            out.append(f"<!--VUEPRESS_END_{container_id}-->\n")

            i += 1
        else:
            out.append(line)
            i += 1

    return "".join(out)


def _restore_container_markers(text: str) -> str:
    """Restore VuePress container markers around formatted content."""
    global _CONTAINER_INFO

    for container in _CONTAINER_INFO:
        container_id = container["id"]
        start_marker = f"<!--VUEPRESS_START_{container_id}-->"
        end_marker = f"<!--VUEPRESS_END_{container_id}-->"

        # Find and replace the markers with VuePress syntax
        start_pos = text.find(start_marker)
        end_pos = text.find(end_marker)

        if start_pos != -1 and end_pos != -1:
            # Extract the formatted content between markers
            content_start = start_pos + len(start_marker)
            content = text[content_start:end_pos]

            # Remove leading/trailing newlines from content for clean formatting
            content = content.strip("\n")

            # Replace the entire section with VuePress container
            vuepress_container = f"{container['start']}\n{content}\n{container['end']}"

            text = text[:start_pos] + vuepress_container + text[end_pos + len(end_marker) :]

    return text


def update_mdit(mdit) -> None:
    """Parser extension - preprocess markdown input."""
    # Store original render method
    original_render = mdit.render

    def patched_render(src, env=None):
        # Extract VuePress containers, leaving content to be formatted
        processed_src = _extract_containers_for_formatting(src)

        # Render normally (this will format the content)
        result = original_render(processed_src, env)

        # Restore VuePress containers around the formatted content
        final_result = _restore_container_markers(result)

        return final_result

    # Replace the render method
    mdit.render = patched_render


# Module-level definitions as expected by mdformat
RENDERERS = {}
CODEFORMATTERS = {}
POSTPROCESSORS = {}
