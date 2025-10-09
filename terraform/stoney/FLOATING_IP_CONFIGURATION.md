# Floating IP Configuration for Ingress Controller

## Overview

Each environment (test, prod) requires a floating IP for the ingress controller to receive external traffic. Terraform manages these IPs differently for each environment.

## How It Works

### ⚠️ IMPORTANT: Manual IP Allocation Required

**Floating IPs must be allocated MANUALLY outside of Terraform** to ensure they persist when you destroy and recreate clusters. This is critical for production use where you want to maintain the same IP for DNS records.

### Why Manual Allocation?

If Terraform manages the floating IP lifecycle:
- ✅ `terraform apply` → Creates IP
- ❌ `terraform destroy` → **DELETES IP** (Bad for production!)
- ❌ DNS records break
- ❌ Need to update DNS after every cluster recreate

If you allocate the IP manually:
- ✅ IP persists across cluster destroy/recreate
- ✅ DNS records remain valid
- ✅ Terraform only validates the IP exists

### Test Environment
- Allocate floating IP manually in OpenStack
- Set in `test.auto.tfvars`:
  ```hcl
  ingress_loadbalancer_ip = "185.85.126.222"
  ```

### Production Environment
- Allocate floating IP manually in OpenStack
- Set in `prod.auto.tfvars`:
  ```hcl
  ingress_loadbalancer_ip = "185.85.126.XXX"
  ```

## Terraform Resources

### IP Lookup (Data Source Only)
```hcl
data "openstack_networking_floatingip_v2" "ingress_ip" {
  count   = var.ingress_loadbalancer_ip != "" ? 1 : 0
  address = var.ingress_loadbalancer_ip
  # Validates that the manually-allocated IP exists
}
```

### Output
```hcl
output "ingress_floating_ip" {
  value = local.ingress_ip
  # Shows the configured IP address
}
```

**Note**: Terraform does NOT create or destroy the floating IP. It only validates that the IP you specified exists in OpenStack.

## Deployment Workflow

### Initial Setup (One-Time Per Environment)

1. **Allocate floating IP manually in OpenStack**:
   ```bash
   # Authenticate with OpenStack
   source ~/path/to/openrc.sh
   
   # Allocate IP for test environment
   openstack floating ip create public \
     --description "aihub-test-ingress-persistent"
   
   # Output shows:
   # | floating_ip_address | 185.85.126.222 |
   
   # Allocate IP for prod environment
   openstack floating ip create public \
     --description "aihub-prod-ingress-persistent"
   
   # Output shows:
   # | floating_ip_address | 185.85.126.XXX |
   ```

2. **Update tfvars with allocated IPs**:
   
   **test.auto.tfvars**:
   ```hcl
   ingress_loadbalancer_ip = "185.85.126.222"
   ```
   
   **prod.auto.tfvars**:
   ```hcl
   ingress_loadbalancer_ip = "185.85.126.XXX"
   ```

3. **Commit the configuration**:
   ```bash
   git add terraform/stoney/{test,prod}.auto.tfvars
   git commit -m "feat: Configure persistent floating IPs for ingress"
   ```

### Deploying Clusters

```bash
# Deploy test cluster
./deploy.sh stoney test apply
# Uses IP: 185.85.126.222 ✅

# Deploy prod cluster
./deploy.sh stoney prod apply
# Uses IP: 185.85.126.XXX ✅
```

### Destroying and Recreating Clusters

```bash
# Destroy cluster (IP remains in OpenStack!)
./deploy.sh stoney test destroy

# Recreate cluster (uses same IP!)
./deploy.sh stoney test apply
# Still uses IP: 185.85.126.222 ✅
# DNS records still work! ✅
```

The floating IP persists in OpenStack and can be reused across cluster recreations.

## Using the IP with Helm

### Option 1: Manual Helm Installation
```bash
helm install nginx-ingress-controller ingress-nginx/ingress-nginx \
  --set controller.service.loadBalancerIP=<FLOATING_IP>
```

### Option 2: Values File
Add to your `values.yaml`:
```yaml
controller:
  service:
    loadBalancerIP: "<FLOATING_IP>"
```

### Option 3: Terraform Output to Helm
You can export the IP and use it in helm:
```bash
export INGRESS_IP=$(terraform output -raw ingress_floating_ip)
helm install ... --set controller.service.loadBalancerIP=$INGRESS_IP
```

## DNS Configuration

After obtaining the floating IP, update your DNS records:

```
# For test environment
*.k8s-test.ai-agents.ch  A  85.85.127.222

# For prod environment (after first deployment)
*.k8s.ai-agents.ch       A  <FLOATING_IP_FROM_TERRAFORM>
```

## Troubleshooting

### Error: "Floating IP not found"
If you set `ingress_loadbalancer_ip` to an IP that doesn't exist:
```
Error: No floating IP found with address: 85.85.XXX.YYY
```

**Solution**: Either allocate the IP manually in OpenStack or set to empty string to auto-allocate.

### Error: "Floating IP already in use"
If the IP is assigned to another resource:
```
Error: Floating IP is already associated
```

**Solution**: Either free up the IP or specify a different IP.

### Check Current IP Status
```bash
# List all floating IPs
openstack floating ip list

# Check specific IP
openstack floating ip show 85.85.127.222

# Check IP for current cluster
cd terraform/stoney
terraform output ingress_floating_ip
```

## State Management

The floating IP is part of the Terraform state:
- **Test state**: `terraform/stoney/test/terraform.tfstate`
- **Prod state**: `terraform/stoney/prod/terraform.tfstate`

Each environment's floating IP is tracked independently.

## Cost Considerations

- Floating IPs typically have a small monthly cost in OpenStack
- Keeping IPs allocated ensures consistent DNS configuration
- If you destroy the infrastructure, consider whether to:
  - Keep the floating IP allocated (costs money but preserves DNS)
  - Release the floating IP (saves money but requires DNS update on next deploy)

## Migration Between Environments

If you need to move a floating IP between environments:

1. **Update the source tfvars** (remove IP):
   ```hcl
   ingress_loadbalancer_ip = ""
   ```

2. **Update the target tfvars** (add IP):
   ```hcl
   ingress_loadbalancer_ip = "85.85.XXX.YYY"
   ```

3. **Apply changes**:
   ```bash
   ./deploy.sh stoney <source-env> apply
   ./deploy.sh stoney <target-env> apply
   ```

## Security Notes

- 🔒 Floating IPs are publicly accessible
- 🔐 Ensure your ingress controller has proper authentication
- 🛡️ Use cert-manager for TLS certificates
- 🚫 Don't expose sensitive services without authentication
- 📝 Document which IPs are allocated to which environments

## Reference

- [OpenStack Floating IP Documentation](https://docs.openstack.org/neutron/latest/admin/intro-os-networking.html#floating-ips)
- [Nginx Ingress Controller LoadBalancer Configuration](https://kubernetes.github.io/ingress-nginx/deploy/)

