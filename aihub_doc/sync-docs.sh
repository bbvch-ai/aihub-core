
#!/bin/bash
#
# This script synchronizes README.md files from the monorepo root
# into the current documentation directory ('aihub_doc').
# It must be run from within 'aihub_doc'.

echo "🔄 Syncing README files..."

# First, clean up old files to avoid duplicates
rm -rf aihub
rm -f LICENSES.md
rm -f CHANGELOG.md

# Remove old synced documentation from 6_code_deep_dive
# This ensures no duplicate index.md/index.en.md files exist
rm -rf docs/6_code_deep_dive/*

mkdir -p "licenses"
mkdir -p "changelog"
cp "../LICENSES.md" "./licenses/index.md"
cp "../CHANGELOG.md" "./changelog/index.md"

# Find all 'README.md' files in the parent directory (../),
# while excluding 'node_modules', '.pytest_cache', '.docker-volumes', and the current 'aihub_doc' directory.
# The output of find is piped to the while loop.
find ../ \( -path '*/node_modules' -o -path '../aihub_doc' -o -path '*/.docker-volumes' -o -path '*/.pytest_cache' -o -path '*/__pycache__' -o -path '*/.mypy_cache' \) -prune -o -type f -name "README.md" -print | while read -r source_file; do
    # 'source_file' is the full path from find, e.g., ../aihub_api/README.md

    dest_file=""

    # == Special Case Handling ==
    # Check if the file is the root README.md.
    if [[ "$source_file" == "../README.md" ]]; then
        # If it is, set the destination to 'aihub/index.md'.
        dest_file="./docs/6_code_deep_dive/1_introduction/index.en.md"
    # Ignore files in .docker-volumes
    elif [[ "$source_file" == *".docker-volumes"* ]]; then
        continue
    # Skip deeply nested README files (more than 2 levels deep in a package)
    # For example: ../aihub_lib/aihub_lib/auth/README.md creates orphaned intermediate dirs
    elif [[ "$source_file" == *"/aihub_"*"/aihub_"*"/"* ]]; then
        continue
    else
        # Otherwise, handle the 'aihub_X' directories.
        # Get the directory of the source file (e.g., ../aihub_api)
        source_dir=$(dirname "$source_file")

        # Remove the leading '../' (e.g., aihub_api)
        relative_dir="${source_dir#../}"

        # Set the final destination path.
        dest_file="./docs/6_code_deep_dive/${relative_dir}/index.en.md"
    fi

    # Get the directory part of the destination path.
    dest_dir=$(dirname "$dest_file")

    # Create the destination directory if it doesn't already exist.
    mkdir -p "$dest_dir"

    # Copy the original file to its new location and name.
    cp "$source_file" "$dest_file"

    echo "  -> Copied '$source_file' to '$dest_file'"
done

echo "✅ Sync complete."