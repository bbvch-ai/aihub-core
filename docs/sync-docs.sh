#!/bin/bash
#
# This script synchronizes README.md files from the monorepo into the
# 'docs/6_code_deep_dive' documentation directory.
# It must be run from within 'docs'.
#
# Scope: ONLY the root README (-> Introduction) and READMEs under 'packages/'
# are published. Other top-level directories (infra/, .github/, .claude/ —
# including .claude/worktrees — etc.) are deliberately NOT synced.

echo "🔄 Syncing README files..."

# First, clean up old files to avoid duplicates
rm -rf swiss-ai-hub
rm -f LICENSE_REPORT.md
rm -f CHANGELOG.md

# Remove old synced documentation from 6_code_deep_dive (except the index files)
# This ensures no duplicate index.md/index.en.md files exist
find docs/6_code_deep_dive -mindepth 1 -maxdepth 1 ! -name 'index.*.md' -exec rm -rf {} +

mkdir -p "licenses"
mkdir -p "changelog"
# Copy LICENSE_REPORT.md as both .en.md and .de.md (no translation needed)
cp "../LICENSE_REPORT.md" "./licenses/index.en.md"
cp "../LICENSE_REPORT.md" "./licenses/index.de.md"
# Copy CHANGELOG.md as both .en.md and .de.md (no translation needed)
cp "../CHANGELOG.md" "./changelog/index.en.md"
cp "../CHANGELOG.md" "./changelog/index.de.md"

# == Root README -> Introduction page ==
root_intro="./docs/6_code_deep_dive/1_introduction/index.en.md"
mkdir -p "$(dirname "$root_intro")"
cp "../README.md" "$root_intro"
# Rewrite image paths for the root README (docs/media/... → ../../../media/...)
sed -i 's|docs/media/|../../../media/|g' "$root_intro"
cp "$root_intro" "${root_intro/.en.md/.de.md}"
echo "  -> Copied '../README.md' to '$root_intro'"

# == Package READMEs ==
# Search ONLY within '../packages'. This intentionally excludes infra/, .github/,
# .claude/ (and its worktrees), and any other top-level directory — they are not
# part of the "code deep dive" of the SDK packages and must not leak into the docs.
find ../packages \( -path '*/node_modules' -o -path '*/.docker-volumes' -o -path '*/.pytest_cache' -o -path '*/__pycache__' -o -path '*/.mypy_cache' -o -path '*/.venv' \) -prune -o -type f -name "README.md" -print | while read -r source_file; do
    # 'source_file' is the full path from find, e.g., ../packages/api/README.md

    # Skip deeply nested package-internal README files
    # (e.g. ../packages/core/swiss_ai_hub/core/auth/README.md creates orphaned intermediate dirs)
    if [[ "$source_file" == *"/packages/"*"/swiss_ai_hub/"* ]]; then
        continue
    fi

    # Get the directory of the source file (e.g., ../packages/api)
    source_dir=$(dirname "$source_file")
    # Remove the leading '../' (e.g., packages/api)
    relative_dir="${source_dir#../}"
    # Set the final destination path.
    dest_file="./docs/6_code_deep_dive/${relative_dir}/index.en.md"

    # Create the destination directory if it doesn't already exist.
    mkdir -p "$(dirname "$dest_file")"

    # Copy the original file to its new location and name.
    cp "$source_file" "$dest_file"
    echo "  -> Copied '$source_file' to '$dest_file'"

    # Also create a .de.md copy (no translation needed for synced READMEs)
    dest_file_de="${dest_file/.en.md/.de.md}"
    cp "$dest_file" "$dest_file_de"
    echo "  -> Duplicated to '$dest_file_de' (no translation)"
done

echo "✅ Sync complete."
