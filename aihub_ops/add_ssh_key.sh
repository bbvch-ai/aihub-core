#!/bin/bash
# Script to add your SSH public key to the instance
# Run this script once you have console or SSH access to the instance

PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB3tPHvM254qcYZHGYBhpZmCbp/UGvE0j46w8QKtbeRD thomas@thomas-Precision-3591"

echo "Adding SSH public key to authorized_keys..."

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add the public key if it's not already there
if ! grep -q "$PUBLIC_KEY" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    echo "✓ SSH key added successfully!"
else
    echo "✓ SSH key already exists in authorized_keys"
fi

echo "You can now SSH using: ssh -i ~/.ssh/swiss_llm_cloud_id_ed25519 ubuntu@83.228.225.209"