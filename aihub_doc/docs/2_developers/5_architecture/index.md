---
title: "High-Level Architecture"
index: 5
---

# :building_construction: Swiss AI-Hub Architecture

::: tip Architecture Overview
The Swiss AI-Hub is built as a comprehensive, event-driven platform that seamlessly integrates AI agents, business processes, and enterprise infrastructure. This architecture enables the creation of transparent, auditable, and sovereign AI solutions that scale from simple assistants to complex autonomous systems.
:::

## :globe_with_meridians: Architectural Principles

### Platform vs. Library Approach

The Swiss AI-Hub follows a **platform-first architecture** rather than a library-based approach:

- **Libraries** help you solve specific problems but leave you to build the infrastructure
- **Platforms** provide the complete environment to solve problems at scale, reliably, and sustainably

Our architecture embodies this philosophy by providing a complete, production-ready ecosystem where developers can focus on creating business value while the platform handles security, scalability, and infrastructure.

### Event-Driven Foundation

The entire system is built on **event-driven architecture** using NATS messaging:

- **Asynchronous Communication**: Services communicate through events, enabling loose coupling
- **Scalability**: Independent scaling of components based on workload
- **Reliability**: Message persistence and replay capabilities for fault tolerance
- **Observability**: Complete audit trail of all system interactions

## :package: Component Architecture

### Infrastructure Layer

The infrastructure layer provides the foundational services that power the entire platform:

| Component | Purpose | Technology | Ports |
|-----------|---------|------------|-------|
| **NATS** | Message broker and event streaming | NATS with JetStream | 4222, 8222 |
| **MongoDB** | Primary database for documents and metadata | MongoDB 8.0 | 27017 |
| **Redis** | Caching and session management | Redis 8.0 | 6379 |
| **PostgreSQL** | Structured data and vector storage | PostgreSQL 17 with pgvector | 5432 |
| **Milvus** | Vector database for embeddings | Milvus 2.5 with etcd/MinIO | 19530, 9091 |
| **Phoenix** | AI observability and tracing | Arize Phoenix | 6006, 4317 |

### AI & Language Models

The platform supports both local and cloud-based AI models:

| Component | Purpose | Technology | Ports |
|-----------|---------|------------|-------|
| **LLaMA.cpp** | Local LLM inference | LLaMA 3.2 1B Instruct | 8182 |
| **Text Embeddings** | Local embedding generation | Alibaba GTE-base-en-v1.5 | 8183 |
| **Open WebUI** | Chat interface and model management | Open WebUI 0.6.13 | 8080 |

### Application Services

The core application services are organized into distinct scopes, each running as independent Docker containers:

#### Core Services
- **API Service** (`aihub_api`): REST API and WebSocket gateway
- **Web Application** (`aihub_web`): Frontend user interface
- **Bot Service** (`aihub_bot`): Integration with collaboration platforms

#### AI Processing Services
- **Agent Services** (`aihub_agent`): Individual AI agents as microservices
- **Process Services** (`aihub_process`): Multi-agent workflow orchestration
- **Pipeline Services** (`aihub_pipeline`): Data ingestion and processing workflows

## :arrows_counterclockwise: Communication Patterns

### NATS-Based Messaging

The system uses sophisticated NATS messaging patterns for service communication:

#### Event Hierarchy
```
BaseEvent
├── ProcessEvent (process control)
├── SemanticEvent (AI operations)
│   ├── LLMEvent
│   ├── AgentEvent
│   └── ChainEvent
├── DisplayEvent (UI updates)
│   ├── ChunkEvent
│   └── ThoughtEvent
└── ControlEvent (lifecycle)
    ├── StartEvent
    ├── StopEvent
    └── ExceptionEvent
```

#### Topic Structure
The system uses hierarchical topic naming for organized message routing:

**Agent Topics:**
```
agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}
```

**Process Topics:**
```
process.{process_class}.{process_id}.{walkthrough_id}.{event_type}.{event_name}.{event_id}
```

### Service Discovery

Services discover each other through structured discovery patterns:
- **Discovery Requests**: Services query for available capabilities
- **Discovery Responses**: Services advertise their capabilities and metadata
- **Health Monitoring**: Continuous service health checks and status updates

## :gear: Service Architecture

### Microservices Design

Each scope (aihub_api, aihub_agent, etc.) is designed as an independent microservice:

#### Scope Structure
```
aihub_{scope}/
├── aihub_{scope}/           # Core implementation
│   ├── runners/            # Service lifecycle management
│   ├── routes/             # API endpoints (if applicable)
│   ├── dispatchers/        # Event handling
│   └── services/           # Business logic
├── playground/             # Development and testing
└── pyproject.toml         # Dependencies and configuration
```

#### Independent Deployment

Each scope can be:
- **Developed independently** with isolated dependencies
- **Tested independently** with scope-specific test suites
- **Deployed independently** as Docker containers
- **Scaled independently** based on workload requirements

### Agent Architecture

Agents are implemented as structured workflows rather than black-box systems:

#### Agent Components
- **Agent Classes**: Core business logic and workflow definitions
- **Agent Configs**: Configuration and parameter management
- **Agent Runners**: Execution environment and lifecycle management
- **Agent Dispatchers**: Event handling and message routing

#### Workflow Transparency
- **Step-by-step execution** with explicit state transitions
- **Automatic tracing** through Phoenix integration
- **Human-readable logs** and audit trails
- **Testable components** with isolated step testing

## :cloud: Deployment Architecture

### Container Orchestration

The platform uses Docker Compose for local development and can be deployed to production using:

#### Local Development
```bash
# CPU-based deployment
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d

# GPU-enabled deployment
docker compose -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml -f docker-compose-gpu.yml up -d
```

#### Production Deployment
- **Kubernetes orchestration** for container management
- **Infrastructure as Code** using Pulumi (aihub_iac)
- **Azure integration** for cloud-native deployment
- **GitOps workflows** for automated deployment

### Scalability Patterns

#### Horizontal Scaling
- **Stateless services** enable horizontal scaling
- **Load balancing** through NATS consumer groups
- **Database sharding** for data layer scaling
- **Cache distribution** using Redis clustering

#### Vertical Scaling
- **GPU acceleration** for AI model inference
- **Memory optimization** for large language models
- **CPU optimization** for processing-intensive tasks

## :shield: Security Architecture

### Defense in Depth

The platform implements multiple layers of security:

#### Network Security
- **Container isolation** through Docker networking
- **Service mesh** for encrypted inter-service communication
- **API gateway** for external access control
- **Private endpoints** for Azure integration

#### Authentication & Authorization
- **OAuth 2.0 / OpenID Connect** for user authentication
- **Role-based access control** (RBAC) for resource authorization
- **API key management** for service-to-service authentication
- **JWT tokens** for stateless authentication

#### Data Protection
- **Encryption at rest** for sensitive data
- **Encryption in transit** for all communications
- **Data sovereignty** with on-premises deployment options
- **Audit logging** for compliance and monitoring

## :chart_with_upwards_trend: Observability Architecture

### Comprehensive Monitoring

#### Application Observability
- **Phoenix Integration**: AI-specific observability and tracing
- **OpenTelemetry**: Distributed tracing across services
- **Structured Logging**: Consistent log format across all services
- **Metrics Collection**: Performance and business metrics

#### Infrastructure Monitoring
- **Health Checks**: Automated service health monitoring
- **Resource Monitoring**: CPU, memory, and storage utilization
- **Network Monitoring**: Inter-service communication metrics
- **Error Tracking**: Centralized error collection and analysis

### Tracing & Debugging

#### AI Workflow Tracing
- **Step-by-step execution** tracking through Phoenix
- **LLM interaction** monitoring and analysis
- **Agent decision** tracking and explanation
- **Process flow** visualization and debugging

#### Performance Analysis
- **Query performance** monitoring for databases
- **Model inference** latency and throughput tracking
- **Cache hit rates** and optimization insights
- **Resource utilization** patterns and optimization

## :zap: Performance Architecture

### Optimization Strategies

#### Database Performance
- **Connection pooling** for efficient database access
- **Query optimization** with proper indexing
- **Read replicas** for scaling read operations
- **Caching strategies** for frequently accessed data

#### AI Model Performance
- **Model quantization** for reduced memory usage
- **Batch processing** for improved throughput
- **GPU acceleration** for intensive computations
- **Model caching** for faster inference

#### Network Performance
- **Message batching** for efficient NATS communication
- **Connection pooling** for HTTP services
- **Content delivery** optimization for web assets
- **Compression** for data transfer optimization

## :twisted_rightwards_arrows: Integration Architecture

### External System Integration

#### Enterprise Systems
- **Active Directory** integration for user management
- **SharePoint** integration for document access
- **Azure services** for cloud-native features
- **REST APIs** for third-party service integration

#### AI Service Integration
- **OpenAI API** for cloud-based LLM access
- **Azure OpenAI** for enterprise AI services
- **Hugging Face** for model repository access
- **Custom models** for specialized use cases

### Data Integration

#### Data Sources
- **Document ingestion** from various file formats
- **Database connectivity** for structured data
- **API integration** for real-time data access
- **Stream processing** for continuous data flows

#### Data Processing
- **ETL pipelines** using Dagster orchestration
- **Real-time processing** through event streams
- **Batch processing** for large data sets
- **Data validation** and quality assurance

## :rocket: Future Architecture Considerations

### Scalability Roadmap

#### Multi-Region Deployment
- **Geographic distribution** for global availability
- **Data replication** across regions
- **Latency optimization** for global users
- **Disaster recovery** and business continuity

#### Advanced AI Features
- **Multi-modal AI** integration (text, image, audio)
- **Federated learning** for privacy-preserving AI
- **Edge deployment** for low-latency applications
- **AI model versioning** and A/B testing

### Evolution Strategy

#### Continuous Innovation
- **Plugin architecture** for extensibility
- **API versioning** for backward compatibility
- **Feature flags** for gradual rollouts
- **Community contributions** through open architecture

This architecture provides a solid foundation for building sophisticated AI applications while maintaining the flexibility to evolve with changing requirements and technological advances.