#!/usr/bin/env python3
"""Deterministic i18n key validation across all locale files.

Compares translation keys across de/en/fr/it locales. Uses English (en)
as the reference locale. Reports missing keys, extra keys, and empty values.

Usage:
    python validate-i18n.py [frontend|backend|all]
    python validate-i18n.py                         # defaults to 'all'
"""

import sys
from collections import defaultdict
from pathlib import Path

import yaml

LOCALES = ["de", "en", "fr", "it"]
REFERENCE_LOCALE = "en"
PROJECT_ROOT = Path(__file__).resolve().parents[4]

FRONTEND_LOCALE_DIR = PROJECT_ROOT / "packages" / "web" / "i18n" / "locales"

BACKEND_TRANSLATION_DIRS = [
    PROJECT_ROOT / "packages" / "core" / "swiss_ai_hub" / "core" / "i18n" / "translations",
    PROJECT_ROOT / "packages" / "api" / "swiss_ai_hub" / "api" / "i18n" / "translations",
    PROJECT_ROOT / "packages" / "agent" / "swiss_ai_hub" / "agent" / "i18n" / "translations",
    PROJECT_ROOT / "packages" / "process" / "swiss_ai_hub" / "process" / "i18n" / "translations",
]


def flatten_keys(data: dict, prefix: str = "") -> dict[str, str]:
    """Flatten nested YAML dict into dot-notation key → value pairs."""
    result = {}
    if not isinstance(data, dict):
        return result
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(flatten_keys(value, full_key))
        else:
            result[full_key] = value
    return result


def find_empty_keys(flat: dict[str, str]) -> list[str]:
    """Return keys whose values are empty or None."""
    return [k for k, v in flat.items() if v is None or (isinstance(v, str) and v.strip() == "")]


def validate_frontend() -> dict:
    """Validate frontend YAML locale files."""
    results = {"area": "frontend", "path": str(FRONTEND_LOCALE_DIR), "locales": {}, "errors": []}

    locale_keys: dict[str, dict[str, str]] = {}
    for locale in LOCALES:
        path = FRONTEND_LOCALE_DIR / f"{locale}.yaml"
        if not path.exists():
            results["errors"].append(f"Missing locale file: {path}")
            continue
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        locale_keys[locale] = flatten_keys(data)

    if REFERENCE_LOCALE not in locale_keys:
        results["errors"].append(f"Reference locale '{REFERENCE_LOCALE}' file not found")
        return results

    ref_keys = set(locale_keys[REFERENCE_LOCALE].keys())

    for locale in LOCALES:
        if locale not in locale_keys:
            continue
        target_keys = set(locale_keys[locale].keys())
        empty = find_empty_keys(locale_keys[locale])
        missing = sorted(ref_keys - target_keys)
        extra = sorted(target_keys - ref_keys)

        total = len(ref_keys)
        present = total - len(missing)
        coverage = (present / total * 100) if total > 0 else 0

        results["locales"][locale] = {
            "total_ref_keys": total,
            "total_keys": len(target_keys),
            "missing": missing,
            "extra": extra,
            "empty": sorted(empty),
            "coverage": round(coverage, 1),
        }

    return results


def discover_backend_groups(base_dir: Path) -> dict[str, dict[str, Path]]:
    """Discover translation file groups under a base directory.

    Returns {scope/name: {locale: path}} grouped by translation name.
    Pattern: {scope}/{name}.{locale}.yml
    """
    groups: dict[str, dict[str, Path]] = defaultdict(dict)
    if not base_dir.exists():
        return groups

    for yml_file in sorted(base_dir.rglob("*.yml")):
        parts = yml_file.stem.rsplit(".", 1)
        if len(parts) != 2:
            continue
        name, locale = parts
        if locale not in LOCALES:
            continue

        scope = yml_file.parent.relative_to(base_dir)
        group_key = f"{scope}/{name}" if str(scope) != "." else name
        groups[group_key][locale] = yml_file

    return groups


def validate_backend_dir(base_dir: Path) -> dict:
    """Validate all translation files under a backend directory."""
    scope_name = base_dir.parents[1].name
    results = {"area": scope_name, "path": str(base_dir), "groups": {}, "errors": []}

    if not base_dir.exists():
        results["errors"].append(f"Directory not found: {base_dir}")
        return results

    groups = discover_backend_groups(base_dir)

    for group_name, locale_paths in sorted(groups.items()):
        group_result = {"locales": {}, "errors": []}

        missing_locales = [l for l in LOCALES if l not in locale_paths]
        if missing_locales:
            group_result["errors"].append(f"Missing locale files: {', '.join(missing_locales)}")

        locale_keys: dict[str, dict[str, str]] = {}
        for locale, path in locale_paths.items():
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            locale_keys[locale] = flatten_keys(data)

        if REFERENCE_LOCALE not in locale_keys:
            group_result["errors"].append(f"Reference locale '{REFERENCE_LOCALE}' not found")
            results["groups"][group_name] = group_result
            continue

        ref_keys = set(locale_keys[REFERENCE_LOCALE].keys())

        for locale in LOCALES:
            if locale not in locale_keys:
                continue
            target_keys = set(locale_keys[locale].keys())
            empty = find_empty_keys(locale_keys[locale])
            missing = sorted(ref_keys - target_keys)
            extra = sorted(target_keys - ref_keys)

            total = len(ref_keys)
            present = total - len(missing)
            coverage = (present / total * 100) if total > 0 else 0

            group_result["locales"][locale] = {
                "total_ref_keys": total,
                "total_keys": len(target_keys),
                "missing": missing,
                "extra": extra,
                "empty": sorted(empty),
                "coverage": round(coverage, 1),
            }

        results["groups"][group_name] = group_result

    return results


def print_frontend_report(result: dict) -> int:
    """Print frontend validation report. Returns number of issues."""
    issues = 0
    print("=" * 70)
    print(f"FRONTEND LOCALES — {result['path']}")
    print("=" * 70)

    for error in result.get("errors", []):
        print(f"  ERROR: {error}")
        issues += 1

    locales = result.get("locales", {})
    if not locales:
        return issues

    print(f"\n{'Locale':<8} {'Ref Keys':<10} {'Keys':<8} {'Missing':<9} {'Extra':<8} {'Empty':<8} {'Coverage':<10}")
    print("-" * 70)

    for locale in LOCALES:
        if locale not in locales:
            continue
        d = locales[locale]
        marker = " *" if locale == REFERENCE_LOCALE else ""
        print(
            f"{locale + marker:<8} {d['total_ref_keys']:<10} {d['total_keys']:<8} "
            f"{len(d['missing']):<9} {len(d['extra']):<8} {len(d['empty']):<8} {d['coverage']}%"
        )
        issues += len(d["missing"]) + len(d["extra"]) + len(d["empty"])

    for locale in LOCALES:
        if locale not in locales or locale == REFERENCE_LOCALE:
            continue
        d = locales[locale]
        if d["missing"]:
            print(f"\n  {locale} — Missing keys ({len(d['missing'])}):")
            for key in d["missing"]:
                print(f"    - {key}")
        if d["extra"]:
            print(f"\n  {locale} — Extra keys ({len(d['extra'])}):")
            for key in d["extra"]:
                print(f"    + {key}")
        if d["empty"]:
            print(f"\n  {locale} — Empty values ({len(d['empty'])}):")
            for key in d["empty"]:
                print(f"    ! {key}")

    return issues


def print_backend_report(result: dict) -> int:
    """Print backend scope report. Returns number of issues."""
    issues = 0
    print(f"\n{'=' * 70}")
    print(f"BACKEND: {result['area']} — {result['path']}")
    print("=" * 70)

    for error in result.get("errors", []):
        print(f"  ERROR: {error}")
        issues += 1

    groups = result.get("groups", {})
    if not groups:
        print("  (no translation files found)")
        return issues

    all_clean = True
    for group_name, group_data in sorted(groups.items()):
        group_issues = 0
        for error in group_data.get("errors", []):
            group_issues += 1

        for locale in LOCALES:
            if locale not in group_data.get("locales", {}):
                continue
            d = group_data["locales"][locale]
            group_issues += len(d["missing"]) + len(d["extra"]) + len(d["empty"])

        if group_issues == 0:
            continue

        all_clean = False
        issues += group_issues
        print(f"\n  [{group_name}]")

        for error in group_data.get("errors", []):
            print(f"    ERROR: {error}")

        locales = group_data.get("locales", {})
        if locales:
            print(
                f"    {'Locale':<8} {'Ref Keys':<10} {'Keys':<8} "
                f"{'Missing':<9} {'Extra':<8} {'Empty':<8} {'Coverage':<10}"
            )
            print(f"    {'-' * 62}")

            for locale in LOCALES:
                if locale not in locales:
                    continue
                d = locales[locale]
                marker = " *" if locale == REFERENCE_LOCALE else ""
                print(
                    f"    {locale + marker:<8} {d['total_ref_keys']:<10} {d['total_keys']:<8} "
                    f"{len(d['missing']):<9} {len(d['extra']):<8} {len(d['empty']):<8} {d['coverage']}%"
                )

            for locale in LOCALES:
                if locale not in locales or locale == REFERENCE_LOCALE:
                    continue
                d = locales[locale]
                if d["missing"]:
                    print(f"      {locale} missing: {', '.join(d['missing'])}")
                if d["extra"]:
                    print(f"      {locale} extra:   {', '.join(d['extra'])}")
                if d["empty"]:
                    print(f"      {locale} empty:   {', '.join(d['empty'])}")

    if all_clean:
        print("  All translation groups have matching keys across locales.")

    return issues


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in ("frontend", "backend", "all"):
        print(f"Usage: {sys.argv[0]} [frontend|backend|all]", file=sys.stderr)
        sys.exit(2)

    total_issues = 0

    if mode in ("frontend", "all"):
        frontend_result = validate_frontend()
        total_issues += print_frontend_report(frontend_result)

    if mode in ("backend", "all"):
        for translation_dir in BACKEND_TRANSLATION_DIRS:
            backend_result = validate_backend_dir(translation_dir)
            total_issues += print_backend_report(backend_result)

    print(f"\n{'=' * 70}")
    if total_issues == 0:
        print("RESULT: All translations are consistent across locales.")
    else:
        print(f"RESULT: {total_issues} issue(s) found across all scopes.")
    print("=" * 70)

    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
