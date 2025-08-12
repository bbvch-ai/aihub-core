import re
from typing import Iterable, Tuple

# Match a VuePress/VitePress container block.
# Start: line beginning with ::: (with any text after it, e.g. "details Title")
# End:   line that's exactly ::: (allowing whitespace)
START_RE = re.compile(r"^[ \t]*:::[^\n]*$", re.M)
END_RE = re.compile(r"^[ \t]*:::[ \t]*$", re.M)

PH = "@@MDFORMAT_VUEPRESS_PLACEHOLDER_{idx}@@"  # single-line sentinel


def _extract_blocks(text: str) -> Tuple[str, list[str]]:
    lines = text.splitlines(keepends=True)
    i, n = 0, len(lines)
    blocks, out = [], []
    while i < n:
        line = lines[i]
        if START_RE.match(line):
            start = i
            i += 1
            while i < n and not END_RE.match(lines[i]):
                i += 1
            if i >= n:
                # no closing; emit the rest unchanged
                out.extend(lines[start:])
                break
            end = i
            block = "".join(lines[start : end + 1])
            blocks.append(block)
            out.append(PH.format(idx=len(blocks) - 1) + "\n")
            i += 1
        else:
            out.append(line)
            i += 1
    return "".join(out), blocks


def _restore_blocks(text: str, blocks: list[str]) -> str:
    for idx, block in enumerate(blocks):
        text = text.replace(PH.format(idx=idx), block)
    return text


def _preprocess(text: str, _path: str) -> Tuple[str, dict]:
    """Runs before mdformat parses the file."""
    stripped, blocks = _extract_blocks(text)
    return stripped, {"_vuepress_blocks": blocks}


def _postprocess(text: str, _path: str, state: dict) -> str:
    """Runs after mdformat renders the file."""
    blocks = state.get("_vuepress_blocks") or []
    if not blocks:
        return text
    return _restore_blocks(text, blocks)


def plugin(md):
    """mdformat plugin entry: register pre/post processors."""
    # mdformat calls these with (text, path) and (text, path, state)
    return {
        "PREPROCESSORS": [_preprocess],
        "POSTPROCESSORS": [_postprocess],
        # no parser/renderer changes needed
    }
