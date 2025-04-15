import os
from pathlib import Path


def find_shared_env_file():
    """Find the shared .env file by traversing up until reaching 'iac_azure' directory"""
    current_dir = Path(os.getcwd())

    # Start from current directory and traverse up
    while current_dir != current_dir.parent:  # Stop at root
        # Check if we've reached the 'iac_azure' directory
        if current_dir.name == "iac_azure":
            shared_env_path = current_dir / ".env.shared"
            if shared_env_path.exists():
                return str(shared_env_path)
            break

        # Check if the parent contains 'iac_azure'
        iac_dir = current_dir / "iac_azure"
        if iac_dir.exists() and iac_dir.is_dir():
            shared_env_path = iac_dir / ".env.shared"
            if shared_env_path.exists():
                return str(shared_env_path)

        # Move up one directory
        current_dir = current_dir.parent

    # Default to local .env if shared file not found
    return ".env"
