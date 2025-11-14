# OpenStack Instance Access Guide

## Instance Information

**swiss-llm-cloud-litellm-proxy**
- **IP Address**: 83.228.225.209 (IPv4), 2001:1600:16:10::d8 (IPv6)
- **Region**: dc4-a (Infomaniak Public Cloud)
- **Status**: ACTIVE
- **Flavor**: a4-ram16-disk50-perf1 (4 vCPUs, 16GB RAM, 50GB Disk)
- **Image**: Ubuntu 22.04 LTS Jammy Jellyfish
- **Current Keypair**: litellm-proxy-key-pair

## Quick Access

### Method 1: OpenStack Console (Recommended)

Get the console URL:
```bash
cd aihub_ops
./access_instance.sh
# Choose option 1
```

Or manually:
```bash
source .env
export OS_CLIENT_CONFIG_FILE=$(pwd)/PCU-VFJXTLP-clouds.yaml
openstack --os-cloud PCP-VFJXTLP-dc4-a console url show c19245dc-8ae8-4e7b-8556-7c41cd4024ea
```

Once in the console:
1. Login as `ubuntu` user
2. Run the following to add your SSH key:
```bash
# Option A: Download and run the script
curl -o add_key.sh https://path/to/add_ssh_key.sh
bash add_key.sh

# Option B: Manual method
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB3tPHvM254qcYZHGYBhpZmCbp/UGvE0j46w8QKtbeRD thomas@thomas-Precision-3591" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Option C: From your GitHub (if you've uploaded your key there)
curl -sL https://github.com/YOUR_USERNAME.keys >> ~/.ssh/authorized_keys
```

### Method 2: SSH Access (After Adding Key)

Once your public key is added to the instance:
```bash
ssh -i ~/.ssh/swiss_llm_cloud_id_ed25519 ubuntu@83.228.225.209
```

## OpenStack CLI Commands

### List all instances
```bash
source .env
export OS_CLIENT_CONFIG_FILE=$(pwd)/PCU-VFJXTLP-clouds.yaml
openstack --os-cloud PCP-VFJXTLP-dc4-a server list
```

### Get instance details
```bash
openstack --os-cloud PCP-VFJXTLP-dc4-a server show swiss-llm-cloud-litellm-proxy
```

### Restart instance
```bash
openstack --os-cloud PCP-VFJXTLP-dc4-a server reboot swiss-llm-cloud-litellm-proxy
```

### View console log
```bash
openstack --os-cloud PCP-VFJXTLP-dc4-a console log show swiss-llm-cloud-litellm-proxy
```

## Registered SSH Keypairs

Your workstation key has been registered in OpenStack:
- **Name**: thomas-workstation-key
- **Type**: ED25519
- **Fingerprint**: 14:b7:c1:17:47:86:a6:d2:a7:3b:83:a5:28:0d:c8:fd

This keypair will be automatically injected into any new instances you create in the dc4-a region (if specified during creation).

## Environment Files

- **`.env`**: Contains OS_PASSWORD and path to your SSH public key
- **`PCU-VFJXTLP-clouds.yaml`**: OpenStack clouds configuration for dc3-a and dc4-a regions

## Security Notes

- The `.env` file contains sensitive credentials - never commit it to git
- Your SSH private key (`~/.ssh/swiss_llm_cloud_id_ed25519`) should have permissions 600
- The instance is accessible via public IP - ensure proper firewall rules are in place

## Troubleshooting

### "Permission denied (publickey)" error
Your public key is not in the instance's `~/.ssh/authorized_keys` file. Use the console method above to add it.

### "Too many authentication failures"
SSH is trying multiple keys. Use `-o IdentitiesOnly=yes`:
```bash
ssh -i ~/.ssh/swiss_llm_cloud_id_ed25519 -o IdentitiesOnly=yes ubuntu@83.228.225.209
```

### Cannot connect to OpenStack API
- Verify `.env` contains correct OS_PASSWORD
- Check network connectivity to https://api.pub1.infomaniak.cloud
- Ensure OpenStack CLI is installed: `pip install python-openstackclient`
