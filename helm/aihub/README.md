# AIHub Helm Chart

This Helm chart deploys the AIHub platform on Kubernetes. AIHub is a comprehensive AI platform that provides various services including OpenWebUI, API services, data storage, and more.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Persistent volume support
- NGINX Ingress Controller
- cert-manager for SSL certificate management

## Installation

1. Configure your environment variables in the values files:
   - Edit `values.yaml` for base configuration
   - Edit `values.nightly.yaml` for nightly image tags
   - Create custom values files for production deployments

2. Install or upgrade the chart:

**⚠️ IMPORTANT**: The base `values.yaml` file does not contain image tags by design. You must use one of the provided values files or specify tags explicitly.

**📁 Note**: All commands assume you start from the project root directory (where `docker-compose.nightly.yml` is located).

For nightly/development release (recommended):
```bash
cd helm/aihub
helm upgrade -i aihub . --namespace aihub --create-namespace --values values.yaml --values values.nightly.yaml
```

For production/stable release (specify your own tags):
```bash
cd helm/aihub
helm upgrade -i aihub . --namespace aihub --create-namespace --values values.yaml --set minio.image.tag=release.2025-05-24t17-08-30z
```

## Uninstallation

```bash
cd helm/aihub
helm uninstall aihub --namespace aihub
```

## Configuration

The chart can be configured using values files. Multiple values files are provided:

- `values.yaml`: Base configuration without image tags (requires additional values file)
- `values.nightly.yaml`: Nightly/development values that provide image tags for nightly builds

### Values Files

The chart uses a tagless base configuration approach for safety:

- **values.yaml**: Contains all configuration except image tags. Includes warnings to prevent accidental deployment without proper tags
- **values.nightly.yaml**: Provides nightly image tags for development/testing
- **Custom values files**: You can create your own values files with specific tags for production

You can use multiple values files by specifying them in order (later files override earlier ones):
```bash
cd helm/aihub
helm upgrade -i aihub . --namespace aihub --create-namespace \
  --values values.yaml \
  --values values.nightly.yaml \
  --values custom-values.yaml
```

### Creating Custom Values Files

For production deployments, create a custom values file with specific tags:

```yaml
# values.production.yaml
minio:
  image:
    tag: "release.2025-05-24t17-08-30z"

postgres:
  image:
    tag: "pg17"

api:
  image:
    tag: "v1.2.3"
```

Then deploy with:
```bash
cd helm/aihub
helm upgrade -i aihub . --namespace aihub --create-namespace \
  --values values.yaml \
  --values values.production.yaml
```

### Key Configuration Options

The chart can be configured using the `values.yaml` file. All environment variables are defined directly in the values files under each service's `env` section.

### Ingress Configuration

The chart creates individual Ingress objects for each service that needs external access. All ingresses use NGINX Ingress Controller with automatic SSL certificate management via cert-manager.

#### Ingress Objects

| Service | Host | Path | Port | Description |
|---------|------|------|------|-------------|
| **Web** | `{{ .Values.global.domain }}` | `/` | 80 | Main web interface with static assets and auth routes |
| **API** | `{{ .Values.global.domain }}` | `/api/v1` | 8000 | API endpoints for the platform |
| **OpenWebUI** | `openwebui.{{ .Values.global.domain }}` | `/` | 8080 | OpenWebUI interface with complex routing for API, static assets, and features |
| **LiteLLM** | `litellm.{{ .Values.global.domain }}` | `/` | 4000 | LiteLLM proxy service |
| **MinIO** | `datalake.{{ .Values.global.domain }}` | `/` | 9001 | MinIO object storage console |
| **Dagster** | `dagster.{{ .Values.global.domain }}` | `/` | 4180 | Dagster data orchestration interface |

#### Ingress Features

- **SSL/TLS**: Automatic certificate management with Let's Encrypt
- **Security Headers**: Comprehensive security headers for all services
- **Path-based Routing**: Complex routing rules for OpenWebUI and Web services
- **Load Balancing**: NGINX-based load balancing and SSL termination
- **Rate Limiting**: Built-in rate limiting and request size limits

#### Prerequisites

Before deploying the chart, ensure you have:
1. NGINX Ingress Controller installed
2. cert-manager installed and configured
3. DNS records pointing to your cluster's external IP

### Global Configuration
- `global.domain`: The domain name for the platform
- `global.logLevel`: Log level for all services
- `global.volumeRoot`: Root path for persistent volumes

### Service Environment Variables

Each service has its own `env` section with default values:

```yaml
minio:
  env:
    MINIO_ROOT_USER: "minioadmin"
    MINIO_ROOT_PASSWORD: "minioadmin123"
    MINIO_URL_SIGNING_SECRET: "your-signing-secret"

postgres:
  env:
    POSTGRES_USER: "postgres"
    POSTGRES_PASSWORD: "postgres123"

api:
  env:
    SUPERUSER_NAME: "admin"
    SUPERUSER_EMAIL: "admin@ai-hub.bbv.ch"
    # ... other API environment variables
```

### Service Configuration
Each service can be enabled/disabled and configured individually:
- `services.minio.enabled`: Enable MinIO object storage
- `services.postgres.enabled`: Enable PostgreSQL database
- `services.redis.enabled`: Enable Redis cache
- `services.openWebui.enabled`: Enable OpenWebUI interface
- `services.api.enabled`: Enable API services
- `services.traefik.enabled`: Enable Traefik reverse proxy

### Environment Variables
All environment variables are managed through the ConfigMap and can be configured in the `values.yaml` file under the `env` section.

## Services

The chart deploys the following services:

- **MinIO**: Object storage for files and data
- **PostgreSQL**: Primary database with pgvector extension
- **Redis**: Caching and session storage
- **MongoDB**: Document database
- **NATS**: Message broker
- **OpenWebUI**: Web interface for AI interactions
- **API**: Core API services
- **Traefik**: Reverse proxy and load balancer
- **LiteLLM**: LLM proxy service
- **Phoenix**: Observability platform
- **Milvus**: Vector database
- **Jupyter**: Code execution environment
- **Playwright**: Web automation
- **Docling**: Document processing
- **Dagster**: Data orchestration

## Persistence

The chart creates persistent volume claims for data that needs to persist across pod restarts:
- MinIO data
- PostgreSQL data
- Redis data
- OpenWebUI data
- Traefik ACME certificates

## Ingress

The chart includes an Ingress resource for external access. It's configured to work with Traefik and includes:
- Automatic HTTPS with Let's Encrypt
- Multiple subdomains for different services
- Security headers and middleware

## Security

The chart includes several security features:
- Non-root containers
- Security contexts
- Network policies (can be enabled)
- Resource limits and requests

## Monitoring

The chart includes observability features:
- Phoenix for tracing and monitoring
- Health checks for all services
- Resource monitoring

## Troubleshooting

### Common Issues

1. **Pod startup failures**: Check the logs and ensure all environment variables are properly set
2. **Database connection issues**: Verify that PostgreSQL is running and accessible
3. **Storage issues**: Ensure persistent volume claims are bound and have sufficient space
4. **Ingress issues**: Check that the ingress controller is running and properly configured

### Logs

To view logs for a specific service:
```bash
kubectl logs -n aihub deployment/aihub-<service-name>
```

### Debugging

To debug a specific pod:
```bash
kubectl exec -it -n aihub <pod-name> -- /bin/bash
```

## Template Organization

The templates are organized by service for better maintainability:

```
templates/
├── _helpers.tpl                    # Common template helpers
├── configmap-env.yaml             # Environment variables ConfigMap
├── ingress.yaml                   # Ingress configuration
├── minio/                         # MinIO service templates
│   ├── minio-deployment.yaml
│   ├── minio-service.yaml
│   ├── minio-pvc.yaml
│   └── minio-entrypoint.yaml
├── postgres/                      # PostgreSQL service templates
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── postgres-pvc.yaml
│   └── postgres-init.yaml
├── api/                          # API service templates
│   ├── api-deployment.yaml
│   └── api-service.yaml
└── ...                           # Other services follow the same pattern
```

Each service folder contains:
- `{service}-deployment.yaml`: Kubernetes Deployment
- `{service}-service.yaml`: Kubernetes Service
- `{service}-pvc.yaml`: Persistent Volume Claim (if needed)
- `{service}-*.yaml`: Additional service-specific resources

## Contributing

When contributing to this Helm chart:
1. Update the version in `Chart.yaml`
2. Test the changes thoroughly
3. Update the documentation
4. Submit a pull request

## License

This chart is licensed under the same license as the AIHub project.
