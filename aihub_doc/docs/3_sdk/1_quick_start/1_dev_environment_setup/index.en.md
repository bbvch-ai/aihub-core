---
title: Development Environment Setup
---

[@mhoegger](https://github.com/mhoegger)

# Development Environment Setup: Your First 15 Minutes with the SDK

Getting started with the Swiss AI Hub SDK is designed to be straightforward. In 15 minutes, you'll have a complete
development environment running with your first custom agent processing real requests.

## Prerequisites Check

Before we begin, ensure you have these tools installed:

**Essential Tools:**

- **Python 3.13** - The SDK requires Python 3.13 for all components
- **Poetry** - For dependency management and virtual environments
- **Docker & Docker Compose** - For running the platform infrastructure
- **make** - For running common development commands

**Optional but Helpful:**

- **Node.js LTS + pnpm** - Only needed for frontend customization
- **Postman** - For API testing and exploration
- **MongoDB Compass** - For database inspection during development

::: tip Quick Install Check
Verify your setup with these commands:

```bash
python --version    # Should show 3.13.x
poetry --version    # Any recent version
docker --version    # Any recent version
make --version      # Any version
```
:::

## Project Setup: 3 Minutes

### Step 1: Create Your Project Structure

Create a new python project and open a terminal in the root of said project.

Initialize a new Poetry project:

```bash
poetry init --no-interaction
```

### Step 2: Install the AI-Hub CLI

The CLI tool automates most setup tasks:

```bash
poetry add --group dev aihub-cli
```

### Step 3: Generate Platform Infrastructure

Create the development infrastructure stack:

```bash
poetry run aihub generate-compose
```

This creates `docker-compose.platform.dev.yml` with all the services you need: NATS messaging, MongoDB, Redis, vector
databases, and the AI-Hub platform components.

### Step 4: Configure Environment

Generate the environment configuration:

```bash
poetry run aihub generate-env
```

This creates `.env.core` with sensible defaults. You'll see placeholder values for OAuth2 configuration - we'll use
development mode for now, so you can leave these as-is for initial testing.

## Start the Platform: 5 Minutes

Launch the complete AI-Hub platform:

```bash
docker compose -f docker-compose-platform.dev.yml --env-file .env.core up -d
```

Wait for all services to start (watch the logs with `docker compose logs -f` if you want to see the startup process).

**Verify the platform is running:**

- Open `http://localhost:8080` - You should see the AI-Hub web interface
- You'll notice no agents are available yet - that's expected!

::: warning Common Startup Issue
If any services fail to start, check that ports 8080, 27017, 6379, and 4222 aren't already in use on your system.
:::

## Create Your First Agent: 5 Minutes

### Step 1: Generate Agent Scaffold

Create your first custom agent:

```bash
poetry run aihub new-agent my_custom_agent
```

This creates a complete agent structure:

```
agents/
├── pyproject.toml              # Shared dependencies
└── my_custom_agent/            # Your agent
    ├── Dockerfile              # Container definition
    ├── main.py                 # Entry point
    └── MyCustomAgent/          # Implementation
        ├── MyCustomAgent.py
        ├── MyCustomAgentConfig.py
        └── events/             # Custom events
```

### Step 2: Examine the Generated Agent

Look at the generated agent code in `agents/my_custom_agent/MyCustomAgent/MyCustomAgent.py`:

```python
# TODO: tbd
```

This agent demonstrates the core SDK patterns:

- **Event-driven steps** with strongly typed inputs and outputs
- **Automatic platform integration** for authentication, tracing, and monitoring
- **Simple business logic** that you can customize for your needs

### Step 3: Start Your Agent

Generate a docker compose file that includes your agent:

```bash
poetry run aihub generate-agent-compose --with-agent my_custom_agent
```

This creates `docker-compose-agents.dev.yml` with your agent configured for development (hot reload included).

Create a basic `.env` file for agent configuration:

Start everything together:

```bash
docker compose \
  -f docker-compose-platform.dev.yml \
  -f docker-compose-agents.dev.yml \
  --env-file .env.core \
  --env-file .env \
  up -d
```

## Test Your Success: 2 Minutes

### Step 1: Verify Agent Registration

Check the web interface at `http://localhost:8080`. You should now see your `my_custom_agent` agent listed in th agents
and is shown as `online`.

### Step 2: Test Agent Interaction

Click on your agent and send a test message. You should receive a response showing your agent processed the request.

### Step 3: Observe Agent Behavior

Visit `http://localhost:6006` to see Phoenix tracing. You'll see detailed traces of your agent's execution, showing each
step and its inputs/outputs.

## What Just Happened?

In 15 minutes, you've achieved something remarkable:

**Complete AI Platform:** You're running a full enterprise AI platform with authentication, monitoring, cost tracking,
and observability.

**Custom Agent Integration:** Your custom agent automatically inherits all platform capabilities - it appears in the web
UI, processes requests, and traces its execution without any additional configuration.

**Development-Ready Environment:** The hot reload setup means you can modify your agent code and see changes immediately
without rebuilding containers.
