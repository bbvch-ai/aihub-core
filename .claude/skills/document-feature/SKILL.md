---
name: document-feature
description: "Create user-facing feature documentation for the VitePress docs site.
  Deep-dives into the codebase, analyzes user value, and produces structured docs.
  Use when user says 'document this feature', 'write feature docs', 'create docs
  for X', 'add feature to docs site', or 'user-facing documentation for'. Takes
  feature name as argument. Outputs VitePress-formatted markdown with TL;DR,
  benefits, setup, and getting started sections."
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write
---

# Document Feature - Create User-Facing VitePress Documentation

Create user-facing documentation for feature "$ARGUMENTS" on the AI-Hub VitePress docs site. Analyzes the codebase to
understand the feature, then produces structured documentation for end users.

## Steps

### 1. Understand the Feature

Search for the feature across all scopes. Answer these questions:

- **Where is it implemented?** Which scopes contain the core logic?
- **How does it work?** Key components and interactions?
- **What APIs does it expose?** REST endpoints, WebSocket events?
- **How do users interact with it?** Web UI, API calls, other?
- **What are its dependencies?** Other features or services?
- **Configuration options?** Customizable behavior?

### 2. Analyze User Value

- What problem does it solve?
- Who is the target user?
- What workflows does it enable?
- What makes it special vs alternatives?
- Measurable benefits (time savings, efficiency)?

### 3. Create Documentation File

**Platform features**: `aihub_doc/docs/2_platform/5_feature_overview/`
**SDK features**: `aihub_doc/docs/3_sdk/1_feature_overview/`

**Required front matter**:
```yaml
---
title: "Feature Title"
index: 1
---
```

**Required document structure**:
1. TL;DR info box (`::: info`)
2. What it is and How it works section
3. Why it is Important section with 5 benefits
4. Collapsible setup/usage details (`::: details`)
5. Getting Started steps

### 4. Verify Consistency

- Compare with existing feature docs for tone and structure
- Reference the MCP Integration docs as a template:
  `aihub_doc/docs/2_platform/5_feature_overview/mcp/index.md`

## VitePress Standards

- Emojis only in h1 and h2 headers, placed at the end
- Use `::: info` for TL;DR, `::: details` for setup, `::: warning` for caveats
- User-facing perspective, present tense, jargon-free language
- Benefit-focused writing -- explain value, not implementation

## Examples

**Typical invocation**:
```
/document-feature RAG Pipeline
```

**Expected output**: A new markdown file at `aihub_doc/docs/2_platform/5_feature_overview/rag-pipeline/index.md` with
full VitePress-formatted documentation including TL;DR, benefits, setup, and getting started.

**Another example**:
```
/document-feature MCP Integration
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Feature spans many scopes | Focus on user-visible behavior, not internal architecture |
| Unsure if platform or SDK feature | If users interact via UI or chat, it is platform; if via code/API, it is SDK |
| No existing template to follow | Use `aihub_doc/docs/2_platform/5_feature_overview/mcp/index.md` as reference |
| Feature is not yet fully implemented | Use `::: warning` boxes to note incomplete sections |

## Done When

- Documentation file created in the correct directory
- All required sections present (TL;DR, What/How, Why, Setup, Getting Started)
- VitePress standards followed (front matter, containers, emoji placement)
- Consistent with existing feature documentation in tone and structure
