---
title: Architecture and Integration
index: 1
---

# Architecture and Integration

The Swiss AI Hub suite interface is built on a sophisticated architectural foundation that enables independent service
development while maintaining a unified user experience. This architecture balances technical flexibility with
operational consistency, allowing organizations to extend capabilities without compromising the integrated suite
paradigm.

## Controller-Based Service Architecture

At the technical foundation of the suite lies a controller-based architecture where each service implements a
standardized controller pattern that defines its API endpoints, permissions, and integration points with the suite
framework.

**Controller as Service Contract**: Each service implements a controller class that serves as its contract with the
suite infrastructure. The controller declares the service's name, description, icon, base routing path, and required
permissions. This standardized interface enables the suite to discover, configure, and present services without
requiring custom integration code for each capability.

**Self-Describing Services**: Controllers expose metadata that enables the suite to present services appropriately.
Service names are internationalized strings available in German, English, French, and Italian. Icons follow standard
iconography conventions, ensuring visual consistency across the interface. Descriptions provide contextual information
that helps users understand each service's purpose.

**Automatic Route Integration**: When a controller is registered with the suite, its routes are automatically mounted
under a standardized `/service/<base-route>` pattern. This convention ensures consistent URL structures across all
services while allowing each controller to define its own internal routing hierarchy. Services can implement complex
nested routing without disrupting the suite's navigation architecture.

**Permission Integration**: Controllers declare the permissions required to access their functionality, integrating
seamlessly with the platform's hierarchical permission system. The suite evaluates user permissions against controller
requirements to determine service visibility and access levels, ensuring users see only authorized capabilities.

## Dynamic Service Discovery

Unlike static application architectures where available features are hardcoded into the interface, the Swiss AI Hub
suite employs dynamic service discovery that adapts to deployment configurations and user authorization states.

**Runtime Service Enumeration**: When a user authenticates, the suite queries the backend to enumerate available
services. This query traverses all registered controllers, evaluates the user's permissions against each service's
requirements, and constructs a personalized service catalog. The interface receives a structured response containing
service metadata and the user's authorization level (standard access or administrative privileges) for each available
service.

**Deployment Flexibility**: Organizations can deploy subsets of the complete suite based on their needs. A focused
deployment might include only agent management and conversation services, while a comprehensive deployment provides the
full range of capabilities. The interface automatically adapts—users see exactly the services deployed in their
environment, with no configuration synchronization required.

**Extensibility Foundation**: When new services are added to a deployment—whether native AI Hub capabilities or custom
organizational extensions—they become immediately available in the suite interface. There is no interface recompilation,
configuration file editing, or manual registration. The service implements the controller pattern, registers itself with
the backend, and the suite discovers and integrates it automatically.

**Session-Aware Updates**: The suite maintains awareness of service availability changes during user sessions. When
administrators modify deployments or adjust user permissions, these changes reflect in the interface upon the user's
next login or explicit session refresh, ensuring users always have current service access without requiring cache
invalidation or manual updates.

## Frontend-Backend Coordination

The suite's unified experience results from sophisticated coordination between frontend interface components and backend
service infrastructure, orchestrated through a well-defined API contract.

**Suite Endpoint**: The backend exposes a dedicated suite endpoint (`/api/v1/suites/`) that serves as the coordination
point between frontend and backend. This endpoint evaluates the authenticated user's permissions, enumerates available
services, and returns a structured response containing service metadata and authorization details.

**Structured Service Metadata**: The suite endpoint returns a JSON structure containing an array of service
descriptions. Each service object includes the service name (localized), description (localized), visual icon
identifier, routing path, and a boolean indicating whether the user has administrative privileges for that service. This
structured response provides everything the frontend needs to render the service navigation and enforce client-side
access controls.

**Caching Strategy**: To optimize performance, the frontend caches suite configuration with a reasonable time-to-live
(typically 5 minutes). This balancing act ensures responsive interface behavior while maintaining reasonable freshness
for permission changes. The cache invalidates automatically when users perform actions that might affect their access,
such as logging out and back in or explicitly refreshing their session.

**Real-Time Synchronization**: For critical operations requiring immediate permission enforcement, the suite supports
real-time synchronization via WebSocket connections. When an administrator revokes a user's access to a service, that
user's session can be notified immediately, triggering an interface update without waiting for cache expiration or
manual refresh.

## Layered Architecture Model

The suite interface implements a layered architecture that separates concerns and enables independent evolution of
different system aspects.

**Presentation Layer**: The topmost layer implements the visual interface—navigation sidebars, service cards, routing
logic, and visual design. This layer consumes the service catalog from the backend and renders an appropriate interface
based on user authorization and deployment configuration. The presentation layer is stateless, deriving its
configuration entirely from backend responses.

**API Gateway Layer**: The middle layer provides the REST API that the presentation layer consumes. This includes the
suite endpoint for service discovery, individual service endpoints for functionality, authentication/authorization
enforcement, and session management. The API gateway routes requests to appropriate service implementations while
applying cross-cutting concerns like logging, tracing, and error handling.

**Service Implementation Layer**: The bottom layer contains the actual service implementations—agent management, thread
management, knowledge management, process automation, and administrative capabilities. Each service is independently
developed and deployed, implementing the controller pattern to integrate with the suite infrastructure.

**Cross-Cutting Infrastructure**: Orthogonal to the layered architecture, cross-cutting infrastructure provides
capabilities used across all layers. This includes authentication/authorization systems, internationalization
frameworks, observability tooling, and data persistence. The infrastructure ensures consistent behavior across all
services without requiring each service to implement common functionality independently.

## Deployment Architecture

The suite supports multiple deployment architectures that balance operational complexity with functional requirements.

**Monolithic Deployment**: In the simplest deployment model, all services run within a single application container.
This approach minimizes operational complexity while providing the complete suite experience. Frontend and backend run
as separate processes (frontend serves the web interface, backend provides the API), but all backend services share a
common runtime environment.

**Microservices Deployment**: For organizations requiring independent service scaling, the architecture supports
decomposition into microservices. Each major service (agents, threads, knowledge, processes) can run as an independent
microservice with its own scaling profile. The suite endpoint coordinates across microservices to assemble the unified
service catalog, presenting the same integrated interface regardless of backend topology.

**Hybrid Deployment**: Organizations can implement hybrid approaches where some services run as integrated components
within a monolith while others operate as independent microservices. The architecture's service discovery mechanism
abstracts deployment topology from the user interface, enabling operational flexibility without interface consequences.

## Technical Foundation

The suite interface builds on modern web technologies selected for reliability, performance, and developer productivity.

**Frontend Framework**: The interface is implemented using Nuxt 3, a Vue.js-based framework that provides server-side
rendering, automatic code splitting, and comprehensive routing capabilities. This foundation enables fast initial page
loads, excellent search engine optimization, and progressive enhancement for varying network conditions.

**Component Library**: Visual components leverage PrimeVue, a comprehensive UI component library that provides rich,
accessible components with consistent styling and behavior. This foundation accelerates development while ensuring
accessibility compliance and cross-browser compatibility.

**State Management**: The frontend employs Pinia Colada for state management, mapping API operations to reactive state.
This approach eliminates boilerplate code while providing automatic caching, request deduplication, and optimistic
updates. Service catalog state, authentication state, and individual service data all flow through this unified state
management system.

**Type Safety**: The entire interface is implemented in TypeScript with strict type checking enabled. API response types
are automatically generated from backend OpenAPI specifications, ensuring type safety across the frontend-backend
boundary and catching integration errors at compile time rather than runtime.

## Competitive Technical Advantages

The suite's architectural approach provides several technical advantages that distinguish the Swiss AI Hub from
alternative AI platforms.

**Zero-Configuration Integration**: Unlike platforms requiring configuration files, environment variables, or manual
registration to add services, the Swiss AI Hub automatically discovers and integrates services through the controller
pattern. This dramatically reduces integration complexity and eliminates configuration drift between deployments.

**Permission-Aware Architecture**: The deep integration between the permission system and service discovery ensures
users never encounter disabled features or access-denied errors for visible interface elements. Services that users
cannot access simply don't appear, creating a clean, focused interface tailored to each user's authorization level.

**Deployment Flexibility**: The architecture's abstraction between service discovery and deployment topology enables
organizations to start with simple deployments and evolve to complex microservices architectures without changing the
user interface or requiring user retraining.

**Evolution Without Disruption**: New services, capability enhancements, and platform extensions integrate seamlessly
without breaking existing functionality or requiring interface redesigns. Organizations' investments in the platform
compound over time as capabilities expand while user experience remains consistent.

This architectural foundation ensures that the Swiss AI Hub suite interface delivers not just a unified experience
today, but a sustainable platform for long-term AI capability evolution that protects organizational investments and
accelerates adoption.
