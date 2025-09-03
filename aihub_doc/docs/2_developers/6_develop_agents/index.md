---
title: Developing Custom Agents
index: 6
---

# Developing Custom Agents

This guide provides step-by-step instructions for setting up a development environment to create your own custom agents. You'll learn how to structure your project, configure dependencies, and test your agents alongside the AI-Hub platform.

## 🏗️ Project Structure Setup

### Base Repository Structure

When developing custom agents in your own repository, follow this recommended structure:

```
your-project/
├── agents/                         # Main agents directory
│   ├── pyproject.toml              # Shared Poetry configuration
│   ├── my_custom_agent/            # Individual agent directory (snake_case)
│   │   ├── Dockerfile              # Agent container definition
│   │   ├── main.py                 # Agent entry point
│   │   └── MyCustomAgent/          # Agent implementation (PascalCase)
│   │       ├── MyCustomAgent.py
│   │       ├── MyCustomAgentConfig.py
│   │       └── events/             # Custom step definitions
│   │           └── ...
│   └── another_agent/              # Additional agents follow same pattern
├── docker-compose.local.yml        # Infrastructure services
└── docker-compose-agents.dev.yml   # Development agent services
```

### Agent Directory Structure

Each agent requires the following essential files:

::: info 📁 Required Files per Agent
- **`Dockerfile`**: Defines the container image for your agent
- **`main.py`**: The entry point that starts your agent service
- **`MyCustomAgent/`**: Directory containing your agent implementation
  - **`MyCustomAgent.py`**: Main agent logic and workflow definition
  - **`MyCustomAgentConfig.py`**: Configuration settings and parameters
  - **`events/`**: Directory for custom step definitions (if needed)
:::

## 🐍 Setting Up Poetry Environment

### Initialize Poetry Project

Navigate to your `agents` directory and create a Poetry project:

```bash
cd agents
poetry init --no-interaction
poetry shell
poetry install
```

### Dependency Management

::: warning ⚠️ Dependency Synchronization
All agents within the same Poetry environment share dependencies. This is intentional and recommended because:

- Updates to AI-Hub core components propagate consistently across all agents
- Collaboration between agents is guaranteed through compatible versions
- Prevents version conflicts that could break inter-agent communication
:::

Add AI-Hub core dependencies to your `pyproject.toml`:

```bash
poetry add aihub-lib aihub-agent
```

## 🐳 Docker Configuration

### Infrastructure Services (docker-compose.local.yml)

Copy the `docker-compose.local.yml` file from the `aihub-core` repository to your project root. This file provides:

::: details 🛠️ Infrastructure Services
- **Third-party services**: NATS, Redis, MongoDB, Dagster
- **AI-Hub platform components**: API, Bot, Web UI
- **Local AI models**: For development and testing
- **Observability tools**: Phoenix tracing, monitoring
:::

::: warning 🔢 Version Compatibility
Ensure the image versions in `docker-compose.local.yml` match your AI-Hub SDK version. Version mismatches can cause compatibility issues between your agents and platform components.
:::

### Agent Services (docker-compose-agents.dev.yml)

Create a separate compose file for your development agents:

```yaml
# docker-compose-agents.dev.yml
version: '3.8'

services:
  my-custom-agent:
    build:
      context: ./agents/my_custom_agent
      dockerfile: Dockerfile
    develop:
      watch:
        - action: sync
          path: ./agents/my_custom_agent
          target: /app/agents/my_custom_agent
          ignore:
            - __pycache__/
            - "*.pyc"
            - "*.pyo"
        - action: rebuild
          path: ./agents/my_custom_agent/Dockerfile
        - action: rebuild
          path: ./agents/my_custom_agent/pyproject.toml
    environment:
      - PYTHONPATH=/app
    networks:
      - aihub-network
    depends_on:
      - nats
      - redis
      - mongodb

networks:
  aihub-network:
    external: true
```

## 🚀 Development Workflow

### Starting the Development Environment

1. **Start Infrastructure Services**:
   ```bash
   docker compose -f docker-compose.local.yml up -d
   ```

2. **Start Your Agents with Watch Mode**:
   ```bash
   docker compose -f docker-compose-agents.dev.yml up --watch
   ```

3. **Monitor Services**:
   ```bash
   docker compose ps
   ```

### Hot Reload Development

::: tip 🔄 Live Code Updates
The development compose file uses Docker Compose's built-in `watch` feature to enable automatic code synchronization and selective rebuilding:

- **Code Sync**: Python source files are automatically synced to the container when changed
- **Smart Rebuilding**: Container is rebuilt only when `Dockerfile` or `pyproject.toml` changes  
- **Performance Optimized**: Ignores cache files (`__pycache__`, `*.pyc`) to prevent unnecessary syncs

This provides fast development cycles with automatic updates when you save code changes.
:::

### Testing Your Agents

With both compose files running:

- **AI-Hub UI**: Access the web interface to interact with your agents
- **API Endpoints**: Test agent functionality through REST API calls  
- **Phoenix Tracing**: Monitor agent execution and debug workflows
- **Direct Integration**: Your agents can communicate with other platform agents



## 🚨 Troubleshooting

### Common Issues

**Version Mismatch Errors**:
- Verify AI-Hub SDK and platform image versions match
- Check dependency versions in `pyproject.toml`

**Network Connectivity**:
- Ensure all services use the same Docker network
- Verify service names match between compose files

**Hot Reload Not Working**:
- Check volume mounts in your compose file
- Verify file watcher is properly configured in your agent

### Development Tools

- **Phoenix UI**: `http://localhost:6006` for tracing and observability
- **AI-Hub Web UI**: `http://localhost:3000` for agent management
- **API Documentation**: `http://localhost:8000/docs` for API testing


