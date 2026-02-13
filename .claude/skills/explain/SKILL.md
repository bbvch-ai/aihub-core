---
name: explain
description: "Analyze and explain code in a specific folder or file. Reads the
  documentation hierarchy, analyzes structure, and provides comprehensive
  explanations. Use when user says 'explain this code', 'what does this do',
  'how does this work', 'walk me through', 'explain folder X', or 'help me
  understand'. Takes a file or folder path as argument. Can identify doc gaps."
allowed-tools: Read, Grep, Glob
---

# Explain Code - Analyze and Explain Any File or Folder

Provide a comprehensive explanation of code at a specific path ($ARGUMENTS). Reads documentation hierarchy, analyzes
code structure, identifies patterns, and explains purpose, architecture, and workflows.

## Steps

### 1. Navigate and Survey

Explore $ARGUMENTS (the target folder or file):

- List all files and subdirectories
- Note the file types, naming patterns, and overall structure
- Identify the scope this code belongs to (aihub_lib, aihub_api, etc.)

### 2. Read the Documentation Hierarchy

Follow README-first approach, from broad to narrow:

1. `/home/user/aihub-core/README.md` (project root)
2. Scope-level README (e.g., `aihub_api/README.md`)
3. Scope-level CLAUDE.md (e.g., `aihub_api/CLAUDE.md`)
4. README in the target directory itself
5. READMEs in subdirectories

### 3. Analyze the Code

Read the actual source files and answer:

- **Primary purpose**: What problem does this solve? Where does it fit in the system?
- **Architecture**: How is it organized? What are the main components/classes?
- **Key workflows**: How does data flow? What are the entry points?
- **Dependencies**: What does this code depend on? What depends on it?

### 4. Identify Documentation Gaps

- Missing READMEs for complex directories
- Inaccurate or outdated docs
- Unclear sections that need improvement

### 5. Provide Comprehensive Explanation

Deliver an in-depth explanation covering:
- Purpose and responsibilities
- Architecture and key components
- Data flow and workflows
- Integration points with other parts of the system
- Any documentation gaps found

## Examples

**Explain a folder**:
```
/explain aihub_api/aihub_api/controller
```
Output: Explanation of all API controllers, their routes, how they connect to services.

**Explain a file**:
```
/explain aihub_agent/aihub_agent/workflow/rag_agent.py
```
Output: Detailed breakdown of the RAG agent workflow, its steps, and LlamaIndex integration.

## README Creation Guidelines

If documentation gaps are found, you may suggest or create READMEs.

**Create when**: folder with multiple files but no README, complex component, standalone functionality.

**Do NOT create when**: folder has very few files, code is self-explanatory, docstrings suffice.

**Writing style**:
- Be VERY concise but complete
- Include "why" not just "what"
- Talk on a high level about philosophy and approach
- DO NOT copy code into READMEs (falls out of sync)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Target path does not exist | Verify the path -- check for typos or use Glob to find it |
| No README in the hierarchy | Rely on code analysis and docstrings instead |
| Code is highly complex | Break explanation into sections per file or component |
| Scope unclear | Check which `pyproject.toml` the file falls under |
