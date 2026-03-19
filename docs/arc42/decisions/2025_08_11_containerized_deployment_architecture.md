# Adopt Containerized Multi-Environment Deployment Architecture

## Context

The Swiss AI Hub platform needed a comprehensive deployment strategy that supports multiple environments (local
development, nightly builds, GPU-enabled deployments, and production-ready configurations) while maintaining the
existing monorepo structure. Previously, deployment configurations were limited and didn't provide clear separation
between different deployment scenarios.

The platform consists of multiple microservices (agents, API, bot, pipelines, web interface) that need to work together
as a cohesive system, but also need flexibility for different deployment environments and resource configurations.

Additionally, the team required a way to build, test, and deploy individual components independently while maintaining
the ability to deploy the complete platform as an integrated solution.

## Decision Drivers

- **Multi-Environment Support**: Need for distinct deployment configurations for development, testing, nightly builds,
  and production environments
- **Resource Optimization**: Different environments require different resource allocations (CPU vs GPU, development vs
  production sizing)
- **Development Workflow**: Support for local development with easy infrastructure setup and teardown
- **CI/CD Integration**: Automated building and deployment of container images with proper versioning
- **Service Independence**: Ability to deploy and scale individual microservices independently
- **Infrastructure as Code**: All deployment configurations should be version-controlled and reproducible
- **Microservice Architecture**: Each component needs its own containerized application entry point

## Decision

We will implement a comprehensive containerized deployment architecture with the following components:

### Decision 1: Multi-Environment Docker Compose Strategy

Create separate Docker Compose files for different deployment scenarios:

1. **Local Development with Pre-built Images** (`infra/docker-compose.local.yml`): For local development/testing using
   registry images with local SSL certificates
2. **Local Development from Source** (`infra/docker-compose.build.yml`): For active development building from source
   with local SSL certificates
3. **Nightly Builds** (`infra/docker-compose.nightly.yml`): For testing latest development builds
4. **Production-Ready** (`infra/docker-compose.latest.yml`): For stable production deployments with Let's Encrypt SSL
5. **GPU-Enabled Deployments** (`infra/docker-compose.*.gpu.yml`): For environments requiring GPU acceleration

### Decision 2: Containerized Application Architecture

Each Swiss AI Hub scope will have dedicated containerized applications:

1. **Agent Applications**: Individual agent containers (e.g., `llm_wrapping_agent`) that can run independently
2. **API Application**: Centralized API container with proper entry points
3. **Bot Application**: Dedicated bot framework container
4. **Pipeline Application**: Dagster-based pipeline container with configuration support
5. **Web Application**: Frontend application container

### Decision 3: Automated Build Pipeline Integration

Implement GitHub Actions workflows for automated container building:

1. **Component-Specific Builds**: Separate workflows for agents, API, bot, pipelines, and web
2. **Version Management**: Support for local, nightly, and tagged version builds
3. **Multi-Architecture Support**: Build containers for different architectures as needed

### Decision 4: Configuration Management Strategy

Standardize configuration management across all services:

1. **Environment-Specific Configs**: Separate configuration files for each deployment environment
2. **Service Discovery**: Consistent naming and networking configuration across services
3. **Infrastructure Services**: Standardized configurations for supporting services (Dagster, LiteLLM, Milvus, NATS,
   PostgreSQL, MinIO)

## Consequences

### Positive

- **Deployment Flexibility**: Teams can choose appropriate deployment configuration for their needs
- **Development Efficiency**: Local development environment can be started with a single command
- **Resource Optimization**: GPU resources only allocated when needed, development environments use minimal resources
- **CI/CD Automation**: Automated building and deployment reduces manual effort and errors
- **Service Independence**: Individual microservices can be developed, tested, and deployed independently
- **Scalability**: Container-based architecture enables horizontal scaling of individual components
- **Consistency**: All environments use the same containerized services, reducing environment-specific bugs

### Negative

- **Complexity**: Multiple Docker Compose files increase configuration maintenance overhead
- **Resource Requirements**: Full platform deployment requires significant local resources (memory, CPU, storage)
- **Learning Curve**: Developers need to understand Docker, compose files, and container orchestration
- **Debug Complexity**: Debugging across multiple containers can be more challenging than monolithic deployment
- **Storage Requirements**: Container images and local volumes consume significant disk space

### Neutral

- **Configuration Management**: Requires discipline to keep environment configurations synchronized
- **Version Coordination**: Need to manage version compatibility across multiple container images
- **Infrastructure Dependencies**: Local development still requires Docker and sufficient system resources
- **Monitoring**: Container-based deployment requires container-aware monitoring and logging approaches

## Implementation Notes

This decision enables:

- Quick environment setup: `docker compose -f docker-compose-gpu.dev.yml up -d`
- GPU acceleration when needed: Use GPU-specific compose files
- Independent service development: Each microservice has its own container and entry point
- Automated deployment: CI/CD pipelines build and deploy containers automatically
- Environment parity: Development, testing, and production use similar container configurations
