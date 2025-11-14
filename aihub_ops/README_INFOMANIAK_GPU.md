# Infomaniak GPU Server Deployment Guide

## Prerequisites

### 1. Install OpenStack CLI

```bash
# Install using pip (Python package)
pip install python-openstackclient

# Or using your system package manager
sudo apt install python3-openstackclient  # Ubuntu/Debian
```

### 2. Set up credentials

Your `clouds.yaml` file is already configured. You need to add your password:

**Option A: Environment variable (recommended for security)**
```bash
export OS_PASSWORD='your-infomaniak-password-here'
```

**Option B: Edit the clouds.yaml file**
```bash
# Edit the password field in PCU-AALAZWD-clouds.yaml
# Replace password: '' with password: 'your-password'
```

### 3. Set the cloud config location

```bash
export OS_CLIENT_CONFIG_FILE=/home/thomas/Projects/aihub-core/aihub_ops/PCU-AALAZWD-clouds.yaml
```

## Quick Start Commands

### Check connection
```bash
# Test connection to dc3-a region
openstack --os-cloud PCP-AALAZWD-dc3-a server list

# Test connection to dc4-a region
openstack --os-cloud PCP-AALAZWD-dc4-a server list
```

### List available GPU flavors
```bash
# Check GPU instances available in dc3-a
openstack --os-cloud PCP-AALAZWD-dc3-a flavor list | grep -i gpu

# Check GPU instances available in dc4-a
openstack --os-cloud PCP-AALAZWD-dc4-a flavor list | grep -i gpu
```

### List available Ubuntu images
```bash
# Find Ubuntu 24.04 image
openstack --os-cloud PCP-AALAZWD-dc3-a image list | grep -i "ubuntu.*24.04"
```

### List networks
```bash
# Find your network ID (needed for deployment)
openstack --os-cloud PCP-AALAZWD-dc3-a network list
```

## Deploy GPU Server

Use the provided deployment script:

```bash
./deploy_infomaniak_gpu.sh
```

Or manually:

```bash
# Replace these values with actual IDs from the commands above
GPU_FLAVOR="<flavor-name-with-gpu>"
IMAGE_ID="<ubuntu-24.04-image-id>"
NETWORK_ID="<your-network-id>"

# Create the server
openstack --os-cloud PCP-AALAZWD-dc3-a server create \
  --flavor "$GPU_FLAVOR" \
  --image "$IMAGE_ID" \
  --network "$NETWORK_ID" \
  --key-name your-ssh-key \
  aihub-gpu-server
```

## Post-Deployment

### SSH into your server
```bash
# Get the IP address
openstack --os-cloud PCP-AALAZWD-dc3-a server show aihub-gpu-server -c addresses

# SSH (replace with actual IP)
ssh ubuntu@<server-ip>
```

### Verify GPU
```bash
# Install NVIDIA drivers (if not pre-installed)
sudo apt update
sudo apt install -y nvidia-driver-550

# Check GPU
nvidia-smi
```

## Useful Commands

### Monitor server creation
```bash
openstack --os-cloud PCP-AALAZWD-dc3-a server show aihub-gpu-server
```

### Delete server
```bash
openstack --os-cloud PCP-AALAZWD-dc3-a server delete aihub-gpu-server
```

### View server logs
```bash
openstack --os-cloud PCP-AALAZWD-dc3-a console log show aihub-gpu-server
```

## Troubleshooting

### "Authentication failed"
- Check your password is correct
- Verify `OS_PASSWORD` environment variable is set

### "No valid host found"
- The flavor might not have available capacity
- Try a different GPU flavor
- Try the other region (dc4-a)

### "Network not found"
- Run `openstack network list` to see available networks
- Use the correct network ID for your project
