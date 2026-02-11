# Claude Code SOTA Enablement

## Context

The aihub-core monorepo had a solid foundation for AI-assisted development with 10 AGENTS.md files, 7 legacy slash
commands in `.claude/commands/`, 2 MCP servers, and 1 global stop hook. However, it was not leveraging the full
capabilities of Claude Code's modern features — Skills system, project-level hooks, custom subagents with memory,
and comprehensive tool scoping.

As the team grows and the platform matures, developer onboarding speed, code quality consistency, and workflow
automation become critical. Claude Code provides mechanisms (Skills, Hooks, Subagents, MCP) that encode development
patterns into reusable, deterministic workflows.

## Decision Drivers

- **Developer productivity**: Reduce onboarding time by encoding all common workflows into invocable skills
- **Deterministic enforcement**: Hooks guarantee formatting, security, and git hygiene automatically
- **Context window efficiency**: Custom subagents with scoped tools prevent context pollution
- **Team standardization**: Skills encode the "right way" to scaffold agents, pipelines, processes, endpoints, pages
- **Platform knowledge preservation**: Subagents with project memory accumulate institutional knowledge
- **Portability**: All configuration lives in the repository, not in individual developer environments

## Decision

Adopt a comprehensive Claude Code enablement strategy:

1. **6 project-level hooks**: Auto-formatting (Python + frontend), sensitive file protection, scope boundary checking,
   git hygiene enforcement, and session initialization
2. **7 migrated skills**: All legacy `.claude/commands/` moved to `.claude/skills/` with proper YAML frontmatter
   (name, description, disable-model-invocation, allowed-tools). Legacy commands directory deleted.
3. **6 scaffolding skills**: New skills encoding platform abstractions (scaffold-agent, scaffold-pipeline,
   scaffold-process, scaffold-api-endpoint, scaffold-frontend-page, scaffold-bot-handler)
4. **8 developer experience skills**: Daily workflow skills (test-scope, docker-dev, check-i18n, generate-sdk,
   dependency-audit, validate-events, debug-agent, release-prep)
5. **7 custom subagents**: Specialized agents with isolated context (codebase-expert, code-reviewer,
   event-flow-analyzer, docker-ops, test-analyzer, frontend-analyzer, documentation-keeper). Three with project memory.
6. **Enhanced MCP**: Added Phoenix MCP server for AI observability access
7. **Infrastructure**: Pre-commit configuration, expanded settings.json with hooks + permissions
8. **Documentation**: This ADR, .claude/README.md, updated AGENTS.md

## Consequences

### Positive

- New developers can scaffold production-ready components by invoking a single skill
- Auto-formatting hooks eliminate style debates and ensure consistent formatting
- Security hooks prevent accidental exposure of credentials
- Custom subagents provide deep specialized knowledge without polluting main context
- Project memory in subagents accumulates institutional knowledge across sessions
- All configuration is version-controlled and portable

### Negative

- Team members need to learn new skill invocations (discoverable via `/skills`)
- Hook scripts add small latency to each tool invocation
- Subagent definitions need maintenance as the codebase evolves
