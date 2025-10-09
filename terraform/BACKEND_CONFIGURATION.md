# Terraform Backend Configuration

## Overview

This Terraform setup uses **separate state files** for each environment (test, prod) to ensure complete isolation. This prevents accidental changes to one environment when working on another.

## How It Works

### Directory Structure

```
terraform/
├── azure/
│   ├── backend-test.hcl       # Backend config for test
│   ├── backend-prod.hcl       # Backend config for prod
│   ├── test/                  # Test state directory
│   │   └── terraform.tfstate
│   ├── prod/                  # Prod state directory
│   │   └── terraform.tfstate
│   ├── test.auto.tfvars       # Test variables
│   ├── prod.auto.tfvars       # Prod variables (if exists)
│   └── main.tf
└── stoney/
    ├── backend-test.hcl       # Backend config for test
    ├── backend-prod.hcl       # Backend config for prod
    ├── test/                  # Test state directory
    │   └── terraform.tfstate
    ├── prod/                  # Prod state directory
    │   └── terraform.tfstate
    ├── test.auto.tfvars       # Test variables
    ├── prod.auto.tfvars       # Prod variables
    └── main.tf
```

### Backend Configuration Files

Each environment has its own backend config file that specifies where the state file is stored:

**backend-test.hcl:**
```hcl
path = "test/terraform.tfstate"
```

**backend-prod.hcl:**
```hcl
path = "prod/terraform.tfstate"
```

## Usage

### Using deploy.sh (Recommended)

The deploy script automatically handles backend configuration:

```bash
# Deploy test environment
./deploy.sh stoney test apply

# Deploy prod environment
./deploy.sh stoney prod apply

# Destroy test environment (only affects test state)
./deploy.sh stoney test destroy

# Destroy prod environment (only affects prod state)
./deploy.sh stoney prod destroy
```

### Manual Terraform Commands

If you need to run terraform commands manually:

```bash
cd terraform/stoney

# For test environment
terraform init -reconfigure -backend-config=backend-test.hcl
terraform plan
terraform apply

# For prod environment
terraform init -reconfigure -backend-config=backend-prod.hcl
terraform plan
terraform apply
```

**Important:** Always run `terraform init -reconfigure -backend-config=backend-<env>.hcl` when switching between environments!

## Benefits

### ✅ Complete Isolation
- Each environment has its own state file
- No risk of cross-environment modifications
- Clear separation of resources

### ✅ Easy to Understand
- Explicit state file locations
- No hidden directories (unlike workspaces)
- Clear which environment you're working with

### ✅ Easy Migration to Remote State
When you're ready to use S3 for state storage, just update the backend config:

**backend-test.hcl (with S3):**
```hcl
bucket = "my-terraform-state"
key    = "aihub/stoney/test/terraform.tfstate"
region = "us-east-1"
```

Then change the backend block in main.tf from `backend "local"` to `backend "s3"`.

### ✅ Works with CI/CD
The deploy.sh script can be used in pipelines:
- Each environment deploys independently
- No workspace management needed
- Clear separation for different pipeline stages

## State File Management

### Backup Your State Files

The state files contain sensitive information and are critical for infrastructure management:

```bash
# Backup all states
tar -czf terraform-state-backup-$(date +%Y%m%d).tar.gz terraform/*/test terraform/*/prod

# Or use git (after adding to .gitignore)
# State files are in .gitignore, so they won't be committed
```

### Recovering from State Loss

If you lose a state file, you'll need to either:
1. Restore from backup
2. Import existing resources: `terraform import <resource_type>.<name> <id>`
3. Recreate the infrastructure (not recommended for production)

## Security Notes

- ⚠️ State files contain **sensitive data** (passwords, keys, etc.)
- 🔒 Never commit state files to git (they're in .gitignore)
- 💾 Keep backups of state files securely
- 🔐 Use remote state (S3, Azure Storage) with encryption for production
- 🚫 Restrict access to state files

## Troubleshooting

### Error: "Backend initialization required"
Run: `terraform init -reconfigure -backend-config=backend-<env>.hcl`

### Error: "State file is for wrong environment"
You likely initialized with the wrong backend config. Run:
```bash
terraform init -reconfigure -backend-config=backend-<correct-env>.hcl
```

### Need to check which state is currently loaded?
```bash
terraform show | grep cluster_name
```

## Migration Guide

If you were using workspaces or a single state file before, here's how to migrate:

### From Single State File
```bash
# 1. Backup current state
cp terraform.tfstate terraform.tfstate.backup

# 2. Initialize with test backend
terraform init -reconfigure -backend-config=backend-test.hcl

# 3. The state will be migrated automatically
```

### From Workspaces
```bash
# 1. Switch to test workspace
terraform workspace select test

# 2. Backup state
cp terraform.tfstate.d/test/terraform.tfstate test/terraform.tfstate

# 3. Reinitialize with backend config
terraform init -reconfigure -backend-config=backend-test.hcl

# 4. Repeat for prod workspace
```

## Additional Configuration

### Floating IP for Ingress Controller

Each environment has its own floating IP configuration for the ingress controller. See `stoney/FLOATING_IP_CONFIGURATION.md` for detailed documentation on:
- How floating IPs are allocated per environment
- Using existing IPs vs allocating new ones
- Configuring the ingress controller with the allocated IP

## Related Documentation

- `stoney/FLOATING_IP_CONFIGURATION.md` - Floating IP management for Stoney cloud deployments
- `azure/` - Azure-specific configuration (uses AKS load balancer)
- `deploy.sh` - Deployment script that handles backend configuration automatically

