
#!/bin/bash
#
# This script synchronizes README.md files from the monorepo root
# into the current documentation directory ('aihub_doc').
# It must be run from within 'aihub_doc'.

echo "🔄 Syncing README files..."

# First, remove the aihub folder
rm -rf aihub
rm -f LICENSES.md
rm -f changelog.md

mkdir -p "licenses"
mkdir -p "changelog"
cp "../LICENSES.md" "./licenses/index.md"
cp "../changelog.md" "./changelog/index.md"

# Find all 'README.md' files in the parent directory (../),
# while excluding 'node_modules' and the current 'aihub_doc' directory.
# The output of find is piped to the while loop.
find ../ -path '*/node_modules' -prune -o -path '../aihub_doc' -prune -o -name "README.md" | while read -r source_file; do
    # 'source_file' is the full path from find, e.g., ../aihub_api/README.md

    dest_file=""

    # == Special Case Handling ==
    # Check if the file is the root README.md.
    if [[ "$source_file" == "../README.md" ]]; then
        # If it is, set the destination to 'aihub/index.md'.
        dest_file="aihub/index.md"
    else
        # Otherwise, handle the 'aihub_X' directories.
        # Get the directory of the source file (e.g., ../aihub_api)
        source_dir=$(dirname "$source_file")

        # Remove the leading '../' (e.g., aihub_api)
        relative_dir="${source_dir#../}"

        # Replace 'aihub_' with 'aihub/' to create the new structure (e.g., aihub/api)
        transformed_dir="${relative_dir/aihub_/aihub/}"

        # Set the final destination path.
        dest_file="${transformed_dir}/index.md"
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