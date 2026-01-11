# Agent 1 - Default Development Agent

This is the default agent development container. Use this for experimentation and learning.

## Access

- **VS Code:** http://localhost:8443
- **OpenCode:** Internal port 8080 (access via `opencode client --server localhost:8080` in VS Code terminal)

## Quick Start

1. **Start the container:**
   ```bash
   docker-compose -f docker-compose.agent-dev.yml up -d agent-1-dev
   ```

2. **Open VS Code in browser:**
   ```
   http://localhost:8443
   ```

3. **Enter password:** `developer` (or your custom password from `.env.agent-dev`)

4. **Open terminal in VS Code**

5. **Connect OpenCode client:**
   ```bash
   opencode client --server localhost:8080
   ```

6. **Tell OpenCode what to build:**
   ```
   You: "Build a simple RAG agent.
        Read /workspace/BUILD_GUIDE.md for architecture.
        Create tests."
   ```

## Development Workflow

### AI-Assisted (90% of work)

```bash
# In VS Code terminal
opencode client --server localhost:8080

You: "Build [description of your agent].
     Read /workspace/BUILD_GUIDE.md for Swiss AI-Hub patterns.
     Follow the guide in /workspace/aihub_agent_guide.md.
     Create full test suite."

# OpenCode builds the agent
# Files appear in VS Code explorer in real-time
```

### Manual Refinement (10% of work)

- Edit files directly in VS Code
- Full Python IntelliSense
- Install extensions (Python, Black, Ruff)
- Use terminal for commands

### Testing

```bash
# Install dependencies (first time only)
poetry install

# Run tests
pytest tests/ -v

# Run agent
python -m trigger
```

### Observability

View agent traces in Phoenix:
```
http://localhost:6006
```

## File Structure

```
/workspace/agent/          # Your agent code (this directory)
├── MyAgent/
│   ├── MyAgent.py         # Agent implementation
│   ├── configs/
│   │   └── MyAgentConfig.py
│   └── events/
│       └── CustomEvent.py
├── tests/
│   └── test_my_agent.py
└── trigger.py             # Test runner
```

## Available Documentation (Inside Container)

- `/workspace/BUILD_GUIDE.md` - Complete agent build guide
- `/workspace/AGENTS.md` - Platform architecture
- `/workspace/aihub_agent_guide.md` - Agent-specific patterns
- `/workspace/aihub_agent/playground/` - Example agents

## Tips

1. **Let AI do the heavy lifting:** OpenCode is great at creating boilerplate, tests, and following patterns

2. **Manual polish:** Use VS Code to refine prompts, tweak thresholds, adjust logic

3. **Iterate:** Alternate between AI assistance and manual editing

4. **Test early:** Run tests frequently to catch issues

5. **Use Phoenix:** Always verify your agent in Phoenix traces

## Common Commands

```bash
# Install new dependency
poetry add langchain

# Format code
poetry run black .

# Lint
poetry run ruff check .

# Type check
poetry run mypy .

# All pre-commit checks
make pr-ready

# Run tests
make test
```

## Help

See full documentation: `/home/user/aihub-core/AGENT_DEV_SETUP.md`
