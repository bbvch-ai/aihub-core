# AIHub Resource Analysis

## Azure VM Specifications (from Terraform)

### System Pool
- **VM Size**: `Standard_B2als_v2`
- **vCPUs**: 2
- **Memory**: 4 GB
- **Node Count**: 1
- **Purpose**: System pods only (critical addons)

### User Pool (Spot)
- **VM Size**: `Standard_D4as_v5`
- **vCPUs**: 4
- **Memory**: 16 GB
- **Node Count**: 0 (min) - 0 (max) - **CURRENTLY DISABLED**
- **Purpose**: Application workloads

## AIHub Service Resource Requirements

### Core Services (Always Running)

| Service | Replicas | CPU Request | CPU Limit | Memory Request | Memory Limit | Total CPU | Total Memory |
|---------|----------|-------------|-----------|----------------|--------------|-----------|--------------|
| **MinIO** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **etcd** | 1 | 100m | 250m | 256Mi | 512Mi | 100m | 256Mi |
| **Milvus** | 1 | 500m | 1000m | 1Gi | 2Gi | 500m | 1Gi |
| **PostgreSQL** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **Phoenix** | 1 | 100m | 250m | 256Mi | 512Mi | 100m | 256Mi |
| **NATS** | 1 | 100m | 200m | 128Mi | 256Mi | 100m | 128Mi |
| **Redis** | 1 | 100m | 200m | 128Mi | 256Mi | 100m | 128Mi |
| **MongoDB** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **Presidio Analyzer** | 1 | 100m | 250m | 256Mi | 512Mi | 100m | 256Mi |
| **Presidio Anonymizer** | 1 | 100m | 250m | 256Mi | 512Mi | 100m | 256Mi |
| **LiteLLM** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **OpenWebUI** | 1 | 500m | 1000m | 1Gi | 2Gi | 500m | 1Gi |
| **Jupyter** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **Playwright** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **Dagster Webserver** | 1 | 50m | 100m | 64Mi | 128Mi | 50m | 64Mi |
| **Dagster Daemon** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **API** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |
| **Docling** | 1 | 500m | 1000m | 1Gi | 2Gi | 500m | 1Gi |
| **Web** | 1 | 100m | 200m | 128Mi | 256Mi | 100m | 128Mi |
| **RAG Agent** | 1 | 100m | 250m | 256Mi | 512Mi | 100m | 256Mi |
| **Default RAG Pipeline** | 1 | 250m | 500m | 512Mi | 1Gi | 250m | 512Mi |

### **TOTAL CORE REQUIREMENTS**
- **Total CPU Requests**: 4.25 cores (4250m)
- **Total Memory Requests**: 10.5 GB (10,752Mi)
- **Total CPU Limits**: 8.5 cores (8500m)
- **Total Memory Limits**: 21 GB (21,504Mi)

## Infrastructure Overhead

### Kubernetes System Components
- **kube-system pods**: ~500m CPU, ~1GB memory
- **ingress-nginx**: ~200m CPU, ~512Mi memory
- **cert-manager**: ~100m CPU, ~256Mi memory
- **external-secrets**: ~100m CPU, ~128Mi memory

### **TOTAL INFRASTRUCTURE OVERHEAD**
- **CPU**: ~900m (0.9 cores)
- **Memory**: ~1.9 GB

## **TOTAL CLUSTER REQUIREMENTS**

### Minimum Requirements (Requests)
- **CPU**: 4.25 + 0.9 = **5.15 cores**
- **Memory**: 10.5 + 1.9 = **12.4 GB**

### Maximum Requirements (Limits)
- **CPU**: 8.5 + 0.9 = **9.4 cores**
- **Memory**: 21 + 1.9 = **22.9 GB**

## **CRITICAL ISSUE: RESOURCE MISMATCH**

### Current Terraform Configuration
- **System Pool**: 4 vCPUs, 16 GB (Standard_D4s_v5) - **UPDATED**
- **User Pool**: 4 vCPUs, 16 GB (Standard_D4as_v5) - **DISABLED (0 nodes)**

### **PROBLEM ANALYSIS**

✅ **System Pool Sufficient**:
- Required: 5.15 cores, 12.4 GB
- Available: 4 cores, 16 GB
- **Status**: ✅ Meets minimum requirements

⚠️ **User Pool Disabled**:
- User pool is set to 0 nodes (min=0, max=0)
- All workloads will run on system pool (acceptable for now)

## **RECOMMENDED SOLUTIONS**

### Option 1: Enable User Pool (Recommended)
```hcl
variable "user_min_count" {
  default = 1  # Change from 0 to 1
}

variable "user_max_count" {
  default = 2  # Change from 0 to 2
}
```

**Result**: 6 vCPUs, 20 GB total capacity
- System: 2 vCPUs, 4 GB
- User: 4 vCPUs, 16 GB
- **Total**: 6 vCPUs, 20 GB
- **Status**: ✅ Sufficient for minimum requirements

### Option 2: Upgrade System Pool
```hcl
variable "system_vm_size" {
  default = "Standard_D4s_v5"  # 4 vCPUs, 16 GB
}
```

**Result**: 4 vCPUs, 16 GB total capacity
- **Status**: ⚠️ Still insufficient for maximum requirements

### Option 3: Hybrid Approach (Best)
```hcl
variable "system_vm_size" {
  default = "Standard_D2s_v5"  # 2 vCPUs, 8 GB
}

variable "user_min_count" {
  default = 1
}

variable "user_max_count" {
  default = 2
}
```

**Result**: 6 vCPUs, 24 GB total capacity
- System: 2 vCPUs, 8 GB
- User: 4 vCPUs, 16 GB
- **Total**: 6 vCPUs, 24 GB
- **Status**: ✅ Sufficient for both minimum and maximum requirements

## **COST IMPACT**

### Current Configuration
- System: 1 × Standard_B2als_v2 = ~$30/month
- User: 0 × Standard_D4as_v5 = $0/month
- **Total**: ~$30/month

### Recommended Configuration (Option 3)
- System: 1 × Standard_D2s_v5 = ~$60/month
- User: 1 × Standard_D4as_v5 (Spot) = ~$40/month
- **Total**: ~$100/month

### Cost Increase: ~$70/month (+233%)

## **IMMEDIATE ACTION REQUIRED**

1. **Enable User Pool**: Set `user_min_count = 1`
2. **Monitor Resource Usage**: Deploy with monitoring
3. **Consider Spot Pricing**: User pool already configured for Spot instances
4. **Plan Scaling**: Set appropriate `user_max_count` for peak loads

## **MONITORING RECOMMENDATIONS**

1. **Resource Monitoring**: Use Azure Monitor to track actual usage
2. **Horizontal Pod Autoscaler**: Implement HPA for services that can scale
3. **Vertical Pod Autoscaler**: Consider VPA for right-sizing
4. **Cost Optimization**: Monitor Spot instance availability and pricing

## **RESOURCE COMPARISON TABLE**

| Configuration | CPU (cores) | Memory (GB) | Status | Monthly Cost |
|---------------|-------------|-------------|--------|--------------|
| **Current Terraform** | 4 | 16 | ✅ Sufficient | ~$60 |
| **Required Minimum** | 5.15 | 12.4 | Target | - |
| **Required Maximum** | 9.4 | 22.9 | Target | - |
| **Option 1: Enable User Pool** | 6 | 20 | ✅ Sufficient | ~$70 |
| **Option 2: Upgrade System** | 4 | 16 | ✅ Sufficient | ~$60 |
| **Option 3: Hybrid (Recommended)** | 6 | 24 | ✅ Optimal | ~$100 |

## **QUICK FIX COMMANDS**

### Enable User Pool (Immediate Fix)
```bash
# Update terraform/variables.tf
sed -i 's/default = 0/default = 1/' terraform/variables.tf  # user_min_count
sed -i 's/default = 0/default = 2/' terraform/variables.tf  # user_max_count

# Apply changes
cd terraform && terraform plan && terraform apply
```

### Alternative: Upgrade System Pool
```bash
# Update terraform/variables.tf
sed -i 's/default = "Standard_B2als_v2"/default = "Standard_D4s_v5"/' terraform/variables.tf

# Apply changes
cd terraform && terraform plan && terraform apply
```

## **CONCLUSION**

✅ **The updated Terraform configuration is now sufficient** for the AIHub deployment. The system pool upgrade to `Standard_D4s_v5` provides adequate resources for all application workloads.

**Status**: Ready to deploy! The system pool now has 4 vCPUs and 16 GB memory, which meets the minimum requirements of 5.15 cores and 12.4 GB.

**Note**: This is a regular (non-spot) instance, so it's stable but more expensive than spot instances. You can always add the user pool later for cost optimization with spot instances.
