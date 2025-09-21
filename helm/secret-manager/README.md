# Secret Manager (External Secrets Operator)

This directory contains the configuration for External Secrets Operator, which provides automatic synchronization between Azure Key Vault and Kubernetes secrets.

## Overview

External Secrets Operator provides:
- Automatic secret synchronization from Azure Key Vault
- Kubernetes-native secret management
- Automatic secret rotation
- Multiple secret store support
- RBAC integration

## Prerequisites

### Azure Setup

1. **Create Azure Key Vault**:
   ```bash
   az keyvault create --name aihub-secrets --resource-group aihub-rg --location westeurope
   ```

2. **Create Service Principal**:
   ```bash
   az ad sp create-for-rbac --name aihub-secret-manager --role "Key Vault Secrets User" --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/aihub-rg/providers/Microsoft.KeyVault/vaults/aihub-secrets
   ```

3. **Store secrets in Key Vault**:
   ```bash
   # MinIO secrets
   az keyvault secret set --vault-name aihub-secrets --name "aihub/minio" --value '{"root-user":"minioadmin","root-password":"secure-password","url-signing-secret":"signing-secret"}'
   
   # PostgreSQL secrets
   az keyvault secret set --vault-name aihub-secrets --name "aihub/postgres" --value '{"username":"postgres","password":"secure-password"}'
   
   # API secrets
   az keyvault secret set --vault-name aihub-secrets --name "aihub/api" --value '{"superuser-name":"admin","superuser-email":"admin@ai-hub.bbv.ch","superuser-oid":"oid","superuser-token":"token","auth-signing-secret":"secret","identity-provider":"azure"}'
   ```

## Installation

### Quick Install

```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

### Manual Install

```bash
# Add the External Secrets Operator Helm repository
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets Operator
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system \
  --create-namespace \
  --values values.yaml
```

## Configuration

### 1. Update Azure Credentials

```bash
# Get the service principal credentials
CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"

# Create the secret
kubectl create secret generic azure-credentials \
  --namespace external-secrets-system \
  --from-literal=client-id="$CLIENT_ID" \
  --from-literal=client-secret="$CLIENT_SECRET"
```

### 2. Update SecretStore

```bash
# Edit the SecretStore with your Azure Key Vault details
kubectl edit secretstore azure-keyvault -n external-secrets-system
```

Update the following fields:
- `tenantId`: Your Azure tenant ID
- `vaultUrl`: Your Azure Key Vault URL
- `clientId`: Your service principal client ID

### 3. Deploy AIHub Secrets

```bash
# Apply the example ExternalSecret resources
kubectl apply -f examples/aihub-secrets.yaml
```

## Usage

### Check Secret Synchronization

```bash
# Check ExternalSecret status
kubectl get externalsecrets -n aihub

# Check synchronized secrets
kubectl get secrets -n aihub

# Check specific secret
kubectl describe secret minio-secrets -n aihub
```

### Monitor Secret Updates

```bash
# Watch ExternalSecret events
kubectl get events -n aihub --watch

# Check ExternalSecret logs
kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets
```

## Secret Structure in Azure Key Vault

### Recommended Key Vault Structure

```
aihub-secrets/
├── aihub/
│   ├── minio
│   │   ├── root-user
│   │   ├── root-password
│   │   └── url-signing-secret
│   ├── postgres
│   │   ├── username
│   │   └── password
│   ├── mongo
│   │   ├── username
│   │   └── password
│   ├── litellm
│   │   ├── master-key
│   │   ├── ui-username
│   │   ├── ui-password
│   │   ├── azure-openai-key
│   │   ├── azure-openai-image-key
│   │   ├── azure-openai-audio-key
│   │   └── gemini-api-key
│   ├── api
│   │   ├── superuser-name
│   │   ├── superuser-email
│   │   ├── superuser-oid
│   │   ├── superuser-token
│   │   ├── auth-signing-secret
│   │   ├── identity-provider
│   │   └── jina-api-key
│   ├── oauth
│   │   ├── provider-name
│   │   ├── client-id
│   │   ├── client-secret
│   │   ├── authority-url
│   │   ├── tenant-id
│   │   └── cookie-secret
│   └── traefik
│       ├── acme-email
│       └── admin-password-hash
```

## Integration with AIHub

### Update AIHub Deployments

Update your AIHub deployment templates to use the synchronized secrets:

```yaml
# Example: MinIO deployment
env:
- name: MINIO_ROOT_USER
  valueFrom:
    secretKeyRef:
      name: minio-secrets
      key: MINIO_ROOT_USER
- name: MINIO_ROOT_PASSWORD
  valueFrom:
    secretKeyRef:
      name: minio-secrets
      key: MINIO_ROOT_PASSWORD
```

## Troubleshooting

### Check External Secrets Operator Status
```bash
kubectl get pods -n external-secrets-system
kubectl get externalsecrets -A
kubectl get secretstores -A
```

### View Logs
```bash
kubectl logs -n external-secrets-system -l app.kubernetes.io/component=operator
kubectl logs -n external-secrets-system -l app.kubernetes.io/component=webhook
```

### Check Secret Store Status
```bash
kubectl describe secretstore azure-keyvault -n external-secrets-system
kubectl describe externalsecret minio-secrets -n aihub
```

### Test Azure Key Vault Access
```bash
# Test from within the cluster
kubectl run test-pod --image=azure-cli --rm -it --restart=Never -- \
  az keyvault secret list --vault-name aihub-secrets
```

## Security Best Practices

1. **Use Managed Identity** (recommended for production):
   ```yaml
   spec:
     provider:
       azurekv:
         tenantId: "YOUR_TENANT_ID"
         vaultUrl: "https://YOUR_VAULT_NAME.vault.azure.net/"
         authSecretRef: {}  # Remove this for managed identity
         servicePrincipal: {}  # Remove this for managed identity
   ```

2. **Rotate secrets regularly** in Azure Key Vault
3. **Use least privilege** for the service principal
4. **Enable audit logging** in Azure Key Vault
5. **Use separate Key Vaults** for different environments

## Uninstallation

```bash
# Remove ExternalSecret resources first
kubectl delete externalsecrets --all -n aihub

# Uninstall External Secrets Operator
helm uninstall external-secrets -n external-secrets-system
kubectl delete namespace external-secrets-system
```

## Resources

- [External Secrets Operator Documentation](https://external-secrets.io/)
- [External Secrets Operator Helm Chart](https://github.com/external-secrets/external-secrets/tree/main/deploy/charts/external-secrets)
- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [External Secrets Operator Azure Provider](https://external-secrets.io/v0.8.6/provider/azure-key-vault/)
