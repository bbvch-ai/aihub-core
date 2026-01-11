# Agent Development Environment - Quick Start

**Get started building AI agents in 5 minutes!**

---

## ⚡ Quick Start (Default Agent)

```bash
# 1. Start the environment
docker-compose -f docker-compose.agent-dev.yml up -d

# 2. Open VS Code in browser
# http://localhost:8443
# Password: developer

# 3. In VS Code terminal, connect OpenCode
opencode client --server localhost:8080

# 4. Tell OpenCode what to build
You: "Build a RAG agent. Read /workspace/BUILD_GUIDE.md for patterns."

# 5. AI builds your agent! ✨
```

---

## 📚 Access Points

| Service | URL | Password |
|---------|-----|----------|
| **VS Code** | http://localhost:8443 | `developer` |
| **Phoenix** | http://localhost:6006 | None |
| **NATS Monitor** | http://localhost:8222 | None |

---

## 🚀 Adding More Agents

### Option 1: Helper Script (Recommended)

```bash
# Add agent #2 for "legal" use case
./deployment/agent-dev/add-agent.sh legal 2

# Start it
docker-compose -f docker-compose.agent-dev.yml up -d agent-2-dev

# Access: http://localhost:8444
```

### Option 2: Manual

1. Uncomment `agent-2-dev` section in `docker-compose.agent-dev.yml`
2. Uncomment volumes: `agent-2-vscode-data`, `agent-2-bash-history`
3. Start: `docker-compose -f docker-compose.agent-dev.yml up -d agent-2-dev`
4. Access: http://localhost:8444

---

## 🎯 Port Reference

| Agent | VS Code | OpenCode | Code Path |
|-------|---------|----------|-----------|
| 1 | 8443 | 8080 | `./agents/agent-1/` |
| 2 | 8444 | 8081 | `./agents/agent-2/` |
| 3 | 8445 | 8082 | `./agents/agent-3/` |
| 4 | 8446 | 8083 | `./agents/agent-4/` |
| 5 | 8447 | 8084 | `./agents/agent-5/` |

---

## 🔧 Common Commands

```bash
# Start all services
docker-compose -f docker-compose.agent-dev.yml up -d

# Start specific agent
docker-compose -f docker-compose.agent-dev.yml up -d agent-1-dev

# View logs
docker-compose -f docker-compose.agent-dev.yml logs -f agent-1-dev

# Stop all
docker-compose -f docker-compose.agent-dev.yml down

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.agent-dev.yml down -v

# Restart agent
docker-compose -f docker-compose.agent-dev.yml restart agent-1-dev

# Enter container shell
docker exec -it agent-1-dev bash
```

---

## 💡 Development Workflow

### 1. AI Builds Foundation (90%)

```
VS Code Terminal → opencode client --server localhost:8080

You: "Build a product inventory RAG agent.
     - Retrieve from Milvus 'products' index
     - Add availability checking
     - Create tests
     Read /workspace/BUILD_GUIDE.md for patterns."

[OpenCode]: Building agent...
[Watch files appear in VS Code in real-time!]
```

### 2. Manual Polish (10%)

- Click on files in VS Code
- Refine prompts, tweak logic
- Save (auto-reloads)

### 3. Test

```bash
# In VS Code terminal
pytest tests/ -v

# Or run trigger script
python -m trigger
```

### 4. View Traces

```
http://localhost:6006
```

### 5. Commit (from host)

```bash
cd /home/user/aihub-core
git add agents/agent-1/
git commit -m "feat(agent): Add product inventory agent"
```

---

## 🔐 Security (Custom Passwords)

```bash
# 1. Copy template
cp .env.agent-dev.template .env.agent-dev

# 2. Edit passwords
nano .env.agent-dev

# Example:
AGENT_1_PASSWORD=my-secure-password-123
AGENT_2_PASSWORD=legal-team-password-456

# 3. Start with env file
docker-compose -f docker-compose.agent-dev.yml --env-file .env.agent-dev up -d
```

**Note:** `.env.agent-dev` is gitignored (passwords safe!)

---

## 📖 Full Documentation

- **Complete Guide:** `AGENT_DEV_SETUP.md`
- **Agent Build Guide:** `AI_AGENT_BUILD_AND_DEPLOY_GUIDE.md`
- **Architecture:** `AGENTS.md`

---

## ❓ Troubleshooting

**VS Code won't load:**
```bash
# Check container is running
docker ps | grep agent-1-dev

# Check logs
docker-compose -f docker-compose.agent-dev.yml logs agent-1-dev
```

**OpenCode not responding:**
```bash
# Restart container
docker-compose -f docker-compose.agent-dev.yml restart agent-1-dev
```

**Code not persisting:**
```bash
# Verify volume mount
docker inspect agent-1-dev | grep -A 5 Mounts

# Should show: ./agents/agent-1 → /workspace/agent
```

---

## 🎉 That's It!

You now have a **scalable, isolated AI agent development environment** where you can:

✅ Build agents with AI assistance (OpenCode)
✅ Polish manually in VS Code
✅ Run 5+ agents simultaneously
✅ All code persists on host
✅ Full observability via Phoenix

**Happy Building! 🚀**
