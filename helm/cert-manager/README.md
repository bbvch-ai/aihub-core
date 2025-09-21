# Cert-Manager

This directory contains the configuration for cert-manager, which provides automatic SSL certificate management for the AIHub platform.

## Overview

Cert-manager provides:
- Automatic SSL certificate provisioning
- Let's Encrypt integration
- Certificate renewal
- Multiple certificate issuers
- Kubernetes-native certificate management

## Installation

### Prerequisites

- Kubernetes cluster (1.19+)
- Helm 3.0+
- kubectl configured to access your cluster
- NGINX Ingress Controller (for HTTP-01 challenges)

### Quick Install

```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

### Manual Install

```bash
# Add the cert-manager Helm repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --values values.yaml
```

## Configuration

The `values.yaml` file contains the configuration for cert-manager:

- **CRD Installation**: Automatic Custom Resource Definition installation
- **Resource Limits**: CPU: 100m, Memory: 128Mi
- **Security**: Non-root user, read-only filesystem
- **Monitoring**: Prometheus metrics support

## ClusterIssuers

The installation creates two ClusterIssuers:

### Production ClusterIssuer
- **Name**: `letsencrypt-prod`
- **Server**: Let's Encrypt production API
- **Rate Limit**: 50 certificates per week per domain
- **Use for**: Production certificates

### Staging ClusterIssuer
- **Name**: `letsencrypt-staging`
- **Server**: Let's Encrypt staging API
- **Rate Limit**: 30,000 certificates per week per domain
- **Use for**: Testing certificate issuance

## Usage

### Request a Certificate

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: aihub-tls
  namespace: aihub
spec:
  secretName: aihub-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.ai-hub.bbv.ch
  - litellm.ai-hub.bbv.ch
  - jupyter.ai-hub.bbv.ch
```

### Ingress with SSL

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aihub-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.ai-hub.bbv.ch
    - litellm.ai-hub.bbv.ch
    secretName: aihub-tls
  rules:
  - host: api.ai-hub.bbv.ch
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aihub-api
            port:
              number: 8000
```

## Troubleshooting

### Check Cert-Manager Status
```bash
kubectl get pods -n cert-manager
kubectl get certificates -A
kubectl get clusterissuers
```

### View Logs
```bash
kubectl logs -n cert-manager -l app.kubernetes.io/component=controller
kubectl logs -n cert-manager -l app.kubernetes.io/component=webhook
kubectl logs -n cert-manager -l app.kubernetes.io/component=cainjector
```

### Check Certificate Status
```bash
kubectl describe certificate aihub-tls -n aihub
kubectl describe certificaterequest -n aihub
```

### Test Certificate Issuance
```bash
# Use staging issuer for testing
kubectl patch certificate aihub-tls -n aihub -p '{"spec":{"issuerRef":{"name":"letsencrypt-staging"}}}'
```

## Email Configuration

Update the email address in the ClusterIssuers:

```bash
kubectl edit clusterissuer letsencrypt-prod
kubectl edit clusterissuer letsencrypt-staging
```

## Uninstallation

```bash
helm uninstall cert-manager -n cert-manager
kubectl delete namespace cert-manager
```

## Resources

- [Cert-Manager Documentation](https://cert-manager.io/docs/)
- [Cert-Manager Helm Chart](https://github.com/cert-manager/cert-manager/tree/master/deploy/charts/cert-manager)
- [Let's Encrypt](https://letsencrypt.org/)
