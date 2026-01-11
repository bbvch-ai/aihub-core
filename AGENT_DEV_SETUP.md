# Agent Development Environment Setup

**Scalable, isolated development containers for building AI agents with VS Code (browser) + OpenCode Server**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Scaling to Multiple Agents](#scaling-to-multiple-agents)
5. [Usage Guide](#usage-guide)
6. [Development Workflow](#development-workflow)
7. [Troubleshooting](#troubleshooting)
8. [Reference](#reference)

---

## Overview

This setup provides **isolated Docker containers** for AI agent development. Each agent gets:

- **VS Code in browser** (code-server) - password protected
- **OpenCode Server** - AI-assisted development
- **Full Python 3.13 + Poetry** environment
- **Access to shared infrastructure** (NATS, Redis, Milvus, Phoenix)
- **Volume-mounted code** - changes persist on host
- **Independent ports** - run 5+ agents simultaneously

### Key Features

✅ **Zero local setup** - Just Docker + browser
✅ **AI + Manual editing** - OpenCode builds, you polish in VS Code
✅ **Scalable** - Easily add more agent dev containers
✅ **Isolated** - Each agent has own environment
✅ **Persistent** - Code saved on host, survives container restarts
✅ **Reproducible** - Dockerfile defines exact environment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Your Browser                                               │
│                                                             │
│  Tab 1: http://localhost:8443  →  Agent 1 (VS Code)       │
│  Tab 2: http://localhost:8444  →  Agent 2 (VS Code)       │
│  Tab 3: http://localhost:8445  →  Agent 3 (VS Code)       │
│  Tab 4: http://localhost:6006  →  Phoenix (Observability) │
│                                                             │
└───────────┬─────────────┬─────────────┬──────────────────────┘
            │             │             │
            ↓             ↓             ↓
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  Agent 1 Dev  │ │  Agent 2 Dev  │ │  Agent 3 Dev  │
│               │ │               │ │               │
│ code-server   │ │ code-server   │ │ code-server   │
│ :8443         │ │ :8443         │ │ :8443         │
│               │ │               │ │               │
│ OpenCode      │ │ OpenCode      │ │ OpenCode      │
│ :8080         │ │ :8080         │ │ :8080         │
│               │ │               │ │               │
│ /workspace/   │ │ /workspace/   │ │ /workspace/   │
│   agent/      │ │   agent/      │ │   agent/      │
│     ↕         │ │     ↕         │ │     ↕         │
│ ./agents/     │ │ ./agents/     │ │ ./agents/     │
│   agent-1/    │ │   legal/      │ │   product/    │
│ (Host)        │ │ (Host)        │ │ (Host)        │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  Shared Infrastructure          │
        │  - NATS (message bus)           │
        │  - Redis (state)                │
        │  - Milvus (vectors)             │
        │  - Phoenix (observability)      │
        │  - PostgreSQL (database)        │
        └─────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Browser** (Chrome, Firefox, Safari, etc.)

### Step 1: Clone Repository

```bash
cd /home/user/aihub-core
```

### Step 2: Configure Passwords (Optional)

```bash
# Copy template
cp .env.agent-dev.template .env.agent-dev

# Edit passwords
nano .env.agent-dev

# Example:
# AGENT_1_PASSWORD=my-secure-password-123
```

If you skip this step, default password is `developer`.

### Step 3: Start Infrastructure + Agent 1

```bash
# Start all services
docker-compose -f docker-compose.agent-dev.yml up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.agent-dev.yml ps

# View logs
docker-compose -f docker-compose.agent-dev.yml logs -f agent-1-dev
```

### Step 4: Access VS Code

```bash
# Open browser
http://localhost:8443

# Enter password: developer (or your custom password)
```

### Step 5: Start Building!

**In VS Code terminal:**

```bash
# Connect OpenCode client
opencode client --server localhost:8080

# Tell AI to build your agent
You: "Build a RAG agent for legal Q&A.
     Read /workspace/BUILD_GUIDE.md for architecture.
     Create full test suite."

# AI builds the agent...
# You see files appear in VS Code explorer!
```

**Or edit manually:**

- Create files in `/workspace/agent/`
- Code persists in `./agents/agent-1/` on your host

---

## Scaling to Multiple Agents

### Method 1: Manual (Copy-Paste)

**Step 1: Edit `docker-compose.agent-dev.yml`**

Uncomment the `agent-2-dev` template section (around line 280):

```yaml
  agent-2-dev:
    container_name: agent-2-dev
    build:
      context: ./deployment/agent-dev
      dockerfile: Dockerfile.agent-dev
      args:
        USERNAME: developer
        USER_UID: 1000
        USER_GID: 1000
    stdin_open: true
    tty: true
    ports:
      - "8444:8443"  # VS Code (incremented from 8443)
      - "8081:8080"  # OpenCode (incremented from 8080)
    volumes:
      - ./agents/agent-2:/workspace/agent:rw
      # ... (rest of volumes same as agent-1)
    environment:
      PASSWORD: ${AGENT_2_PASSWORD:-developer}
      AGENT_NAME: agent-2
      VSCODE_PORT: 8444
      OPENCODE_PORT: 8081
      # ... (rest of env vars same)
    depends_on:
      # ... (same as agent-1)
    networks:
      - agent-dev-network
```

**Step 2: Uncomment volume:**

```yaml
volumes:
  agent-1-vscode-data:
  agent-1-bash-history:
  agent-2-vscode-data:  # Uncomment this
  agent-2-bash-history: # Uncomment this
```

**Step 3: Start agent 2:**

```bash
docker-compose -f docker-compose.agent-dev.yml up -d agent-2-dev
```

**Step 4: Access:**

```
http://localhost:8444  (Agent 2 VS Code)
```

### Method 2: Using Helper Script

**Step 1: Use the helper script:**

```bash
# Add a new agent called "legal"
./deployment/agent-dev/add-agent.sh legal 2

# This creates agent-2-dev with:
# - VS Code: http://localhost:8444
# - OpenCode: http://localhost:8081
# - Code in: ./agents/legal/
```

**Step 2: Start it:**

```bash
docker-compose -f docker-compose.agent-dev.yml up -d agent-2-dev
```

### Port Assignment Reference

| Agent | Service Name | VS Code Port | OpenCode Port | Code Path |
|-------|-------------|--------------|---------------|-----------|
| 1 | `agent-1-dev` | 8443 | 8080 | `./agents/agent-1/` |
| 2 | `agent-2-dev` | 8444 | 8081 | `./agents/agent-2/` |
| 3 | `agent-3-dev` | 8445 | 8082 | `./agents/agent-3/` |
| 4 | `agent-4-dev` | 8446 | 8083 | `./agents/agent-4/` |
| 5 | `agent-5-dev` | 8447 | 8084 | `./agents/agent-5/` |

### Example: 5 Agents Running Simultaneously

```yaml
# docker-compose.agent-dev.yml (simplified view)

services:
  # Infrastructure (shared)
  nats: ...
  redis: ...
  milvus: ...
  phoenix: ...

  # Agent 1: General dev
  agent-1-dev:
    ports: ["8443:8443", "8080:8080"]
    volumes: ["./agents/agent-1:/workspace/agent"]
    environment:
      PASSWORD: ${AGENT_1_PASSWORD}

  # Agent 2: Legal RAG
  agent-2-dev:
    ports: ["8444:8443", "8081:8080"]
    volumes: ["./agents/legal:/workspace/agent"]
    environment:
      PASSWORD: ${AGENT_2_PASSWORD}

  # Agent 3: Product inventory
  agent-3-dev:
    ports: ["8445:8443", "8082:8080"]
    volumes: ["./agents/product:/workspace/agent"]
    environment:
      PASSWORD: ${AGENT_3_PASSWORD}

  # Agent 4: Customer support
  agent-4-dev:
    ports: ["8446:8443", "8083:8080"]
    volumes: ["./agents/support:/workspace/agent"]
    environment:
      PASSWORD: ${AGENT_4_PASSWORD}

  # Agent 5: Experimental
  agent-5-dev:
    ports: ["8447:8443", "8084:8080"]
    volumes: ["./agents/experimental:/workspace/agent"]
    environment:
      PASSWORD: ${AGENT_5_PASSWORD}
```

**Access all 5:**

```
Agent 1: http://localhost:8443
Agent 2: http://localhost:8444
Agent 3: http://localhost:8445
Agent 4: http://localhost:8446
Agent 5: http://localhost:8447
Phoenix: http://localhost:6006
```

---

## Usage Guide

### Connecting to VS Code

1. **Open browser:** `http://localhost:8443` (or 8444, 8445, etc.)
2. **Enter password:** `developer` (or your custom password)
3. **You're in VS Code!**

### Using OpenCode (AI Assistant)

**In VS Code terminal:**

```bash
# Connect OpenCode client
opencode client --server localhost:8080

# Natural language commands
You: "Build a RAG agent for product inventory.
     Read /workspace/BUILD_GUIDE.md for architecture.
     Use Milvus index 'products'.
     Add tests."

[OpenCode]: Reading documentation...
[OpenCode]: Creating ProductAgent.py...
[OpenCode]: Tests created!

# You see files update in VS Code in real-time!
```

### Manual Editing

Just use VS Code normally:

- **Explorer:** Navigate files
- **Editor:** Write code (full Python IntelliSense)
- **Terminal:** Run commands (`poetry install`, `pytest`, etc.)
- **Extensions:** Install Python, Black, Ruff extensions

### Running Your Agent

**Method 1: Via trigger script**

```bash
# In VS Code terminal
cd /workspace/agent
python -m trigger

# Agent runs and publishes events to Phoenix
```

**Method 2: Via tests**

```bash
pytest tests/test_my_agent.py -v
```

**Method 3: Via OpenCode**

```
You: "Run the agent with test query: 'What is product X?'"

[OpenCode]: Running trigger script...
[OpenCode]: Response: [agent output]
```

### Viewing Traces (Phoenix)

```
http://localhost:6006

- See all agent executions
- View step-by-step workflow
- Inspect LLM calls, retrievals, errors
```

---

## Development Workflow

### Typical Session: Building Legal RAG Agent

**1. Start container:**

```bash
docker-compose -f docker-compose.agent-dev.yml up -d agent-2-dev
```

**2. Open VS Code:**

```
http://localhost:8444
Password: (from .env.agent-dev)
```

**3. AI builds foundation (90%):**

```bash
# VS Code terminal
opencode client --server localhost:8080

You: "Build a Legal RAG agent with citations.
     Read /workspace/BUILD_GUIDE.md for how agents work.

     Requirements:
     - Retrieve from Milvus 'legal_docs' index
     - Track citations with document IDs
     - Add confidence scoring
     - Create BDD tests
     - Make production-ready"

[OpenCode]: Reading BUILD_GUIDE.md...
[OpenCode]: Creating LegalRAGAgent/LegalRAGAgent.py...
[OpenCode]: Creating configs/LegalRAGAgentConfig.py...
[OpenCode]: Creating events/CitationEvent.py...
[OpenCode]: Writing tests/features/legal_rag.feature...
[OpenCode]: Writing tests/test_legal_rag.py...
[OpenCode]: Running poetry install...
[OpenCode]: Running make pr-ready... ✓
[OpenCode]: Running make test... ✓
[OpenCode]: Agent complete!
```

**4. Manual polish (10%):**

Edit in VS Code:

```python
# File: LegalRAGAgent/LegalRAGAgent.py
# AI wrote:
prompt = "Answer based on documents"

# You refine:
prompt = """You are a Swiss legal assistant.
Answer ONLY based on provided legal documents.
Include citation numbers [1], [2] in your answer.

Documents:
{context}

Question: {query}

Answer with citations:"""
```

**5. Test:**

```bash
python -m trigger

# Or
pytest tests/ -v
```

**6. View traces:**

```
http://localhost:6006
```

**7. Iterate:**

```
You: "Add reranking to improve relevance"

[OpenCode]: Adding reranking step...
[OpenCode]: Updated!
```

**8. Commit (from host):**

```bash
cd /home/user/aihub-core

# Code is in ./agents/legal/ (persisted)
git add agents/legal/
git commit -m "feat(agent): Add legal RAG agent with citations"
git push
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose -f docker-compose.agent-dev.yml logs agent-1-dev

# Common issues:
# - Port already in use (change ports in docker-compose.yml)
# - Infrastructure not healthy (wait 60s after first start)
```

### Can't access VS Code

```bash
# Check container is running
docker ps | grep agent-1-dev

# Check port mapping
docker port agent-1-dev

# Verify password
echo $AGENT_1_PASSWORD
```

### OpenCode not responding

```bash
# Check OpenCode is running
docker exec -it agent-1-dev ps aux | grep opencode

# Restart container
docker-compose -f docker-compose.agent-dev.yml restart agent-1-dev
```

### Code changes not persisting

Verify volume mount:

```bash
# Check volume binding
docker inspect agent-1-dev | grep -A 5 Mounts

# Should show: ./agents/agent-1 → /workspace/agent
```

### Poetry dependencies missing

```bash
# In VS Code terminal
cd /workspace
poetry install

# If Poetry not found
export PATH="/opt/poetry/bin:$PATH"
poetry install
```

### Agent can't connect to infrastructure

```bash
# Check infrastructure health
docker-compose -f docker-compose.agent-dev.yml ps

# All should be "healthy"

# Check network
docker exec -it agent-1-dev ping nats
docker exec -it agent-1-dev ping redis
```

---

## Reference

### Files Created

```
/home/user/aihub-core/
├── docker-compose.agent-dev.yml     # Main compose file
├── .env.agent-dev.template          # Password template
├── .env.agent-dev                   # Your passwords (gitignored)
├── AGENT_DEV_SETUP.md              # This guide
├── deployment/agent-dev/
│   ├── Dockerfile.agent-dev        # Container definition
│   ├── start-services.sh           # Startup script
│   └── add-agent.sh                # Helper to add agents
└── agents/                          # Your agent code
    ├── agent-1/                     # Agent 1 (default)
    ├── agent-2/                     # Agent 2 (if added)
    └── ...
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENT_1_PASSWORD` | VS Code password for agent 1 | `developer` |
| `AGENT_2_PASSWORD` | VS Code password for agent 2 | `developer` |
| `VOLUME_ROOT` | Docker volumes location | `./.docker-volumes` |
| `NATS_URL` | NATS connection string | `nats://nats:4222` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `MILVUS_HOST` | Milvus hostname | `milvus` |

### Useful Commands

```bash
# Start all services
docker-compose -f docker-compose.agent-dev.yml up -d

# Start specific agent
docker-compose -f docker-compose.agent-dev.yml up -d agent-2-dev

# Stop all
docker-compose -f docker-compose.agent-dev.yml down

# View logs
docker-compose -f docker-compose.agent-dev.yml logs -f agent-1-dev

# Restart agent
docker-compose -f docker-compose.agent-dev.yml restart agent-1-dev

# Rebuild after Dockerfile changes
docker-compose -f docker-compose.agent-dev.yml build agent-1-dev

# Enter container shell
docker exec -it agent-1-dev bash

# List all agents
docker-compose -f docker-compose.agent-dev.yml ps

# Remove all volumes (fresh start)
docker-compose -f docker-compose.agent-dev.yml down -v
```

### Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Agent 1 VS Code | http://localhost:8443 | Development IDE |
| Agent 2 VS Code | http://localhost:8444 | Development IDE |
| Agent 3 VS Code | http://localhost:8445 | Development IDE |
| Phoenix | http://localhost:6006 | Observability |
| NATS Monitor | http://localhost:8222 | Message bus status |

### Documentation References

- **Agent Architecture:** `/workspace/BUILD_GUIDE.md` (inside container)
- **Swiss AI Agent Protocol:** `/workspace/AGENTS.md`
- **aihub_agent Guide:** `/workspace/aihub_agent_guide.md`
- **Examples:** `/workspace/aihub_agent/playground/`

---

## Next Steps

1. **Start with Agent 1:** Get familiar with the workflow
2. **Build a simple agent:** Use OpenCode to create a basic workflow
3. **Add more agents:** Scale to 2-3 agents for different use cases
4. **Explore Phoenix:** Understand observability and tracing
5. **Contribute:** Share your agent designs with the team

**Happy Agent Building! 🚀**
