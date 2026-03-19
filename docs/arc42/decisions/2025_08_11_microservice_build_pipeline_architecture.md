# Adopt Component-Specific CI/CD Build Pipeline Architecture

## Context

The Swiss AI Hub platform consists of multiple distinct components (agents, API, bot, pipelines, web) that previously
shared a monolithic build process. As the platform matured, the need arose for more granular build control, allowing
individual components to be built, tested, and deployed independently while maintaining integration capabilities.

The existing CI/CD pipeline was insufficient for:

- Building individual microservices with different dependencies and requirements
- Supporting multiple deployment environments (local, nightly, GPU, production)
- Managing version coordination across components
- Optimizing build times by only rebuilding changed components

The monorepo structure needed to be preserved while enabling component-specific build optimization and deployment
flexibility.

## Decision Drivers

- **Component Independence**: Each microservice should have its own build pipeline with appropriate dependencies
- **Version Management**: Support for different versioning strategies (local development, nightly builds, semantic
  versioning)
- **Environment Flexibility**: Build artifacts suitable for different deployment environments
- **Parallel Processing**: Enable concurrent building of independent components
- **Resource Optimization**: Different components have different build requirements (Node.js vs Python vs
  container-only)
- **Deployment Coordination**: Maintain ability to deploy complete platform while enabling component-specific
  deployments

## Decision

We will implement a component-specific CI/CD build pipeline architecture with the following structure:

### Decision 1: Component-Specific Build Workflows

Create dedicated GitHub Actions workflows for each major component:

1. **Agent Builds** (`build-agents.yml`): Build all agent containers and applications
2. **API and Bot Builds** (`build-api-and-bot.yml`): Build API and bot services together due to shared dependencies
3. **Pipeline Builds** (`build-pipelines.yml`): Build Dagster-based data processing pipelines
4. **Dagster Builds** (`build-dagster.yml`): Build Dagster orchestration containers
5. **Web Builds** (`build-web.yml`): Build frontend applications with Node.js-specific pipeline

### Decision 2: Centralized Build Action with Component Parameters

Extend the existing `build_image` action to support component-specific parameters:

1. **Flexible Path Support**: Allow specification of build context and Dockerfile paths
2. **Multi-Stage Builds**: Support complex build scenarios with multiple stages
3. **Registry Management**: Consistent image naming and registry push strategies
4. **Version Coordination**: Coordinate version tags across all component builds

### Decision 3: Event-Driven Build Coordination

Implement repository dispatch events for coordinating builds:

1. **Chain Dependencies**: Use `repository_dispatch` instead of `workflow_run` for better workflow independence
2. **Structured Job Coordination**: Break complex workflows into discrete, coordinatable jobs
3. **Conditional Execution**: Enable conditional building based on changed components

### Decision 4: Multi-Environment Build Support

Support building for different deployment environments:

1. **Local Development Builds**: Quick builds for local testing
2. **Nightly Builds**: Automated builds from latest development branch
3. **Release Builds**: Versioned builds for production deployment
4. **Feature Branch Builds**: On-demand builds for testing specific features

## Consequences

### Positive

- **Build Efficiency**: Only changed components are rebuilt, significantly reducing CI/CD time
- **Parallel Processing**: Independent components can be built concurrently, improving overall build speed
- **Component Isolation**: Build failures in one component don't block others
- **Resource Optimization**: Each build workflow uses only the resources needed for that component
- **Deployment Flexibility**: Components can be deployed independently or as a complete platform
- **Development Velocity**: Teams can iterate faster on individual components without full platform rebuilds
- **Clear Separation**: Each component's build requirements and dependencies are explicitly defined

### Negative

- **Complexity**: Multiple build workflows require more maintenance and coordination
- **Version Management**: Coordinating versions across multiple components becomes more complex
- **Integration Testing**: Need additional processes to ensure component compatibility
- **Build Configuration Duplication**: Some configuration may be duplicated across workflows
- **Debugging Overhead**: Troubleshooting build issues requires understanding multiple workflow files

### Neutral

- **Monitoring Requirements**: Need comprehensive monitoring across all component build pipelines
- **Documentation**: Requires clear documentation of build dependencies and coordination
- **Tooling**: Development tools need to understand the component-specific build structure
- **Testing Strategy**: Need both component-specific and integration testing approaches

## Implementation Notes

This decision enables:

- **Targeted Builds**: `gh workflow run build-agents.yml` to build only agent components
- **Environment-Specific Deployment**: Different components can be built for different environments
- **Rapid Iteration**: Developers can quickly test changes to specific components
- **Scalable Architecture**: New components can easily be added with their own build pipelines
- **Resource Efficiency**: Build resources are allocated based on actual component needs

The architecture maintains the benefits of the monorepo (shared dependencies, coordinated releases) while providing the
flexibility of component-specific build and deployment capabilities.
