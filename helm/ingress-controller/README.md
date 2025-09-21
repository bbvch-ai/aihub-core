# NGINX Ingress Controller

This directory contains the configuration for the NGINX Ingress Controller used by the AIHub platform.

## Overview

The NGINX Ingress Controller provides:
- HTTP/HTTPS load balancing
- SSL termination
- Rate limiting
- Request routing
- Monitoring and metrics

## Installation

### Prerequisites

- Kubernetes cluster (1.19+)
- Helm 3.0+
- kubectl configured to access your cluster

### Quick Install

```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

### Manual Install

```bash
# Add the NGINX Ingress Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress Controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --values values.yaml
```

## Configuration

The `values.yaml` file contains the configuration for the NGINX Ingress Controller:

- **Service Type**: LoadBalancer (for Azure AKS)
- **Resource Limits**: CPU: 500m, Memory: 512Mi
- **Replica Count**: 2 (for high availability)
- **Rate Limiting**: 100 requests per minute
- **SSL Configuration**: TLS 1.2 and 1.3 support
- **Logging**: Structured JSON logs

## Azure-Specific Configuration

The configuration includes Azure-specific annotations:
- `service.beta.kubernetes.io/azure-load-balancer-internal: "false"`
- `service.beta.kubernetes.io/azure-dns-label-name: "aihub-ingress"`

## Monitoring

The controller exposes metrics on port 10254:
- Prometheus metrics available at `/metrics`
- ServiceMonitor can be enabled for Prometheus Operator

## SSL Certificates

For SSL certificates, install cert-manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

## Usage with AIHub

After installing the NGINX Ingress Controller, you can deploy AIHub:

```bash
helm upgrade -i aihub ./helm/aihub \
  --namespace aihub \
  --create-namespace \
  --values values.yaml \
  --values values.nightly.yaml
```

## Troubleshooting

### Check Controller Status
```bash
kubectl get pods -n ingress-nginx
kubectl get service -n ingress-nginx
```

### View Logs
```bash
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Check External IP
```bash
kubectl get service ingress-nginx-controller -n ingress-nginx
```

## Uninstallation

```bash
helm uninstall ingress-nginx -n ingress-nginx
kubectl delete namespace ingress-nginx
```

## Resources

- [NGINX Ingress Controller Documentation](https://kubernetes.github.io/ingress-nginx/)
- [NGINX Ingress Helm Chart](https://github.com/kubernetes/ingress-nginx/tree/main/charts/ingress-nginx)
- [Azure AKS Ingress](https://docs.microsoft.com/en-us/azure/aks/ingress-basic)
