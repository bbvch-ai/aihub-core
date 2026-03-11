#!/usr/bin/env python3
"""Rewrite imports from core to use the public interface (__init__.py)."""

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path("/home/joelbarmettler/projects/aihub/aihub-core")
CORE_ROOT = REPO_ROOT / "packages/core/swiss_ai_hub/core"
PACKAGES_TO_REWRITE = ["api", "bot", "pipeline", "process"]


# ── helpers ────────────────────────────────────────────────────────────────

def parse_all_exports() -> dict[str, dict[str, str]]:
    """Parse core __init__.py files.

    Returns: {import_path: {symbol_name: source_module}} from _LAZY_IMPORTS,
    plus the __all__ list as keys with empty source for non-lazy inits.
    """
    result = {}
    for init_file in sorted(CORE_ROOT.rglob("__init__.py")):
        if "__pycache__" in str(init_file):
            continue
        parts = list(init_file.parent.relative_to(CORE_ROOT.parent.parent.parent).parts)
        idx = parts.index("swiss_ai_hub")
        import_path = ".".join(parts[idx:])

        content = init_file.read_text()
        symbols = {}

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "_LAZY_IMPORTS":
                            if isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value.values):
                                    if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                        symbols[k.value] = v.value
                        elif isinstance(target, ast.Name) and target.id == "__all__":
                            if isinstance(node.value, ast.List):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant) and elt.value not in symbols:
                                        symbols[elt.value] = ""
        except Exception:
            pass

        if symbols:
            result[import_path] = symbols

    return result


def build_symbol_map(exports: dict[str, dict[str, str]]) -> dict[str, str]:
    """Build symbol_name -> shortest public import path.

    Prefers shorter paths (swiss_ai_hub.core.events.agent over
    swiss_ai_hub.core.events.agent.display).
    """
    symbol_map = {}
    # Sort by path length (shortest first) so shorter paths win
    for pkg_path in sorted(exports, key=lambda p: p.count(".")):
        for sym in exports[pkg_path]:
            if sym not in symbol_map:
                symbol_map[sym] = pkg_path
    return symbol_map


def collect_needed_imports() -> dict[str, set[tuple[str, str]]]:
    """Collect all imports from core in target packages.

    Returns: {file_path: set of (module_path, symbol_name)}
    """
    result = {}
    import_re = re.compile(r"from (swiss_ai_hub\.core\.\S+) import")

    for pkg in PACKAGES_TO_REWRITE:
        pkg_dir = REPO_ROOT / f"packages/{pkg}"
        for py_file in pkg_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text()
            except Exception:
                continue

            file_imports = set()
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("swiss_ai_hub.core."):
                        for alias in node.names:
                            file_imports.add((node.module, alias.name))
            except Exception:
                # Fallback to regex for files that don't parse
                for match in import_re.finditer(content):
                    module_path = match.group(1)
                    # Get the rest of the line after "import"
                    rest_start = match.end()
                    rest = content[rest_start:].split("\n")[0].strip()
                    if rest.startswith("("):
                        # Multi-line import
                        end = content.find(")", rest_start)
                        if end > 0:
                            rest = content[rest_start:end]
                    for sym in re.split(r"[,\s()]+", rest):
                        sym = sym.strip()
                        if sym and sym.isidentifier():
                            file_imports.add((module_path, sym))

            if file_imports:
                result[str(py_file)] = file_imports

    return result


def find_missing_symbols(
    needed: dict[str, set[tuple[str, str]]],
    symbol_map: dict[str, str],
) -> dict[str, dict[str, str]]:
    """Find symbols not yet in any __init__.py.

    Returns: {target_init_path: {symbol: source_module}}
    """
    missing = defaultdict(dict)

    all_symbols = set()
    for file_imports in needed.values():
        for module_path, sym in file_imports:
            all_symbols.add((module_path, sym))

    for module_path, sym in all_symbols:
        if sym not in symbol_map:
            # Determine target __init__.py: swiss_ai_hub.core.<subpackage>
            parts = module_path.split(".")
            if len(parts) >= 3:
                target = ".".join(parts[:3])
            else:
                target = module_path
            missing[target][sym] = module_path

    return dict(missing)


def add_exports_to_init(init_path: str, additions: dict[str, str]) -> None:
    """Add symbols to a core __init__.py file."""
    parts = init_path.split(".")
    idx = parts.index("swiss_ai_hub")
    rel_parts = parts[idx:]
    file_path = REPO_ROOT / "packages/core" / "/".join(rel_parts) / "__init__.py"

    if not file_path.exists():
        print(f"  WARNING: {file_path} does not exist!")
        return

    content = file_path.read_text()

    if "_LAZY_IMPORTS" not in content:
        # Need to create the lazy import pattern from scratch
        tc_imports = "\n".join(
            f"    from {src} import {sym}" for sym, src in sorted(additions.items())
        )
        all_entries = ",\n".join(f'    "{sym}"' for sym in sorted(additions))
        lazy_entries = "\n".join(
            f'    "{sym}": "{src}",' for sym, src in sorted(additions.items())
        )
        new_content = f'''from typing import TYPE_CHECKING

if TYPE_CHECKING:
{tc_imports}

__all__ = [
{all_entries},
]

_LAZY_IMPORTS = {{
{lazy_entries}
}}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {{__name__!r}} has no attribute {{name!r}}"
    raise AttributeError(msg)
'''
        file_path.write_text(new_content)
        return

    # Add to existing file
    for sym, src in sorted(additions.items()):
        # Add TYPE_CHECKING import
        tc_line = f"    from {src} import {sym}"
        if tc_line not in content:
            # Find end of TYPE_CHECKING block
            tc_match = re.search(r"if TYPE_CHECKING:\n((?:    from .+\n)+)", content)
            if tc_match:
                insert_pos = tc_match.end()
                content = content[:insert_pos] + tc_line + "\n" + content[insert_pos:]

        # Add to __all__
        all_entry = f'    "{sym}",'
        if all_entry not in content and f'"{sym}"' not in content.split("_LAZY_IMPORTS")[0].split("__all__")[-1]:
            all_match = re.search(r"__all__\s*=\s*\[\n", content)
            if all_match:
                insert_pos = all_match.end()
                content = content[:insert_pos] + all_entry + "\n" + content[insert_pos:]

        # Add to _LAZY_IMPORTS
        lazy_entry = f'    "{sym}": "{src}",'
        if lazy_entry not in content:
            lazy_match = re.search(r"_LAZY_IMPORTS\s*(?::\s*[^=]+=|=)\s*\{\n", content)
            if lazy_match:
                insert_pos = lazy_match.end()
                content = content[:insert_pos] + lazy_entry + "\n" + content[insert_pos:]

    file_path.write_text(content)


def rewrite_file(file_path: str, file_imports: set[tuple[str, str]], symbol_map: dict[str, str]) -> bool:
    """Rewrite imports in a single file."""
    path = Path(file_path)
    content = path.read_text()
    original = content

    # Parse the file to find ImportFrom nodes with their line positions
    try:
        tree = ast.parse(content)
    except Exception:
        return False

    lines = content.splitlines(keepends=True)

    # Collect all import statements that need rewriting
    # Group by: old_module -> [(symbol, new_module)]
    rewrites_needed = {}
    for module_path, sym in file_imports:
        if sym in symbol_map and symbol_map[sym] != module_path:
            if module_path not in rewrites_needed:
                rewrites_needed[module_path] = {}
            rewrites_needed[module_path][sym] = symbol_map[sym]

    if not rewrites_needed:
        return False

    # Simple approach: for each old import path, replace with the new one
    # This handles the case where all symbols from one module go to the same target
    for old_module, sym_targets in rewrites_needed.items():
        # Group symbols by target module
        target_groups = defaultdict(list)
        for sym, target in sym_targets.items():
            target_groups[target].append(sym)

        # Also find symbols that DON'T need rewriting (stay with old module)
        all_syms_from_module = {sym for mod, sym in file_imports if mod == old_module}
        staying_syms = all_syms_from_module - set(sym_targets.keys())

        # Build regex to match the import statement
        # Match both single-line and multi-line imports
        escaped_mod = re.escape(old_module)

        # Try multi-line first
        multi_pattern = re.compile(
            rf"from {escaped_mod} import \((.*?)\)",
            re.DOTALL,
        )
        single_pattern = re.compile(
            rf"from {escaped_mod} import ([^\n(]+)",
        )

        def build_replacement(staying, target_groups_local):
            parts = []
            if staying:
                syms = sorted(staying)
                if len(syms) <= 3:
                    parts.append(f"from {old_module} import {', '.join(syms)}")
                else:
                    inner = ",\n".join(f"    {s}" for s in syms)
                    parts.append(f"from {old_module} import (\n{inner},\n)")

            for target, syms in sorted(target_groups_local.items()):
                syms = sorted(syms)
                if len(syms) <= 3:
                    parts.append(f"from {target} import {', '.join(syms)}")
                else:
                    inner = ",\n".join(f"    {s}" for s in syms)
                    parts.append(f"from {target} import (\n{inner},\n)")

            return "\n".join(parts)

        replacement = build_replacement(staying_syms, target_groups)

        # Try multi-line replacement first
        if multi_pattern.search(content):
            content = multi_pattern.sub(replacement, content, count=1)
        elif single_pattern.search(content):
            content = single_pattern.sub(replacement, content, count=1)

    if content != original:
        path.write_text(content)
        return True
    return False


# ── main ───────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    print("Step 1: Parsing core exports...")
    exports = parse_all_exports()
    symbol_map = build_symbol_map(exports)
    print(f"  {len(symbol_map)} symbols available via public interface")

    print("\nStep 2: Collecting imports from target packages...")
    needed = collect_needed_imports()
    total_imports = sum(len(v) for v in needed.values())
    print(f"  {total_imports} import references across {len(needed)} files")

    print("\nStep 3: Finding missing symbols...")
    missing = find_missing_symbols(needed, symbol_map)
    total_missing = sum(len(v) for v in missing.values())
    print(f"  {total_missing} symbols need to be added to core __init__.py files:")
    for target, additions in sorted(missing.items()):
        print(f"    {target}: {sorted(additions.keys())}")

    if dry_run:
        print("\n=== DRY RUN - no changes made ===")
        return

    if total_missing > 0:
        print("\nStep 4: Adding missing exports to core __init__.py files...")
        for target, additions in sorted(missing.items()):
            add_exports_to_init(target, additions)
            print(f"  Updated {target} (+{len(additions)})")

        # Rebuild symbol map
        exports = parse_all_exports()
        symbol_map = build_symbol_map(exports)
        print(f"  Now {len(symbol_map)} symbols available")

    print("\nStep 5: Rewriting imports...")
    files_changed = 0
    for pkg in PACKAGES_TO_REWRITE:
        pkg_changes = 0
        for file_path, file_imports in needed.items():
            if f"packages/{pkg}/" in file_path:
                if rewrite_file(file_path, file_imports, symbol_map):
                    pkg_changes += 1
        files_changed += pkg_changes
        print(f"  {pkg}: {pkg_changes} files updated")

    print(f"\nTotal: {files_changed} files updated")


if __name__ == "__main__":
    main()
