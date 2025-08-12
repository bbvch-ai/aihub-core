# mdformat_vuepress/plugin.py
import re
from typing import List

# --- container detection ---
START_RE = re.compile(r"^[ \t]*:::[^\n]*$", re.M)
END_RE = re.compile(r"^[ \t]*:::\s*$", re.M)

# Global storage for VuePress blocks during processing
_VUEPRESS_BLOCKS = []


def _extract_blocks(text: str) -> str:
    """Extract VuePress containers and replace with placeholders."""
    global _VUEPRESS_BLOCKS
    _VUEPRESS_BLOCKS = []

    lines = text.splitlines(keepends=True)
    i, n = 0, len(lines)
    out = []

    while i < n:
        line = lines[i]
        if START_RE.match(line):
            start = i
            i += 1

            # Look for matching end
            while i < n and not END_RE.match(lines[i]):
                i += 1

            if i >= n:
                out.extend(lines[start:])
                break

            # Found matching end
            end = i
            block = "".join(lines[start : end + 1])
            idx = len(_VUEPRESS_BLOCKS)
            _VUEPRESS_BLOCKS.append(block)

            # Replace with a special marker that won't interfere with markdown parsing
            out.append(f'<div data-vuepress-container="{idx}"></div>\n')
            i += 1
        else:
            out.append(line)
            i += 1

    return "".join(out)


def _restore_blocks(text: str) -> str:
    """Restore VuePress containers from placeholders."""
    global _VUEPRESS_BLOCKS

    for idx, block in enumerate(_VUEPRESS_BLOCKS):
        placeholder = f'<div data-vuepress-container="{idx}"></div>'
        if placeholder in text:
            text = text.replace(placeholder, block.rstrip("\n"))

    return text


def update_mdit(mdit) -> None:
    """Parser extension - preprocess markdown input."""
    # Store original render method
    original_render = mdit.render

    def patched_render(src, env=None):
        # Extract VuePress blocks before parsing
        processed_src = _extract_blocks(src)

        # Render normally
        result = original_render(processed_src, env)

        # Restore VuePress blocks
        final_result = _restore_blocks(result)

        return final_result

    # Replace the render method
    mdit.render = patched_render


# Module-level definitions as expected by mdformat
RENDERERS = {}
CODEFORMATTERS = {}
POSTPROCESSORS = {}
