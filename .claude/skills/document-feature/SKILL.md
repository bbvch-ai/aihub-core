---
name: document-feature
description: Create user-facing feature documentation for the VitePress docs site.
  Deep-dives into the codebase, analyzes user value, and produces structured
  documentation following platform standards.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write
---

# Document Features - Create User-Facing Feature Documentation

Create user-facing documentation for feature "$ARGUMENTS" in the AI-Hub.

## Process

1. Deep-dive into the codebase to understand the feature
2. Analyze user value and business impact
3. Create structured documentation following VitePress standards
4. Ensure consistency with existing feature docs

## Step 1: Understand the Feature

Search for the feature across all scopes. Answer:

- **Where is it implemented?** Which scopes contain the core logic?
- **How does it work?** Key components and interactions?
- **What APIs does it expose?** REST endpoints, WebSocket events?
- **How do users interact with it?** Web UI, API calls, other?
- **What are its dependencies?** Other features or services it relies on?
- **Configuration options?** Can users customize behavior?

## Step 2: Analyze User Value

- What problem does it solve?
- Who is the target user?
- What workflows does it enable?
- What makes it special vs alternatives?
- Measurable benefits (time savings, efficiency)?

## Step 3: Create Documentation

Create in either:
- `aihub_doc/docs/2_platform/5_feature_overview/` (platform features)
- `aihub_doc/docs/3_sdk/1_feature_overview/` (SDK features)

Required front matter:
```yaml
---
title: "Feature Title"
index: 1
---
```

Required structure: TL;DR info box, What/How section, Why Important section with 5 benefits, collapsible setup/usage details, Getting Started steps.

## VitePress Standards

- Emojis only in h1 and h2 headers, at the end
- Use `::: info` for TL;DR, `::: details` for setup, `::: warning` for caveats
- User-facing perspective, present tense, jargon-free language, benefit-focused
- Reference the MCP Integration docs as a template:
  `aihub_doc/docs/2_platform/5_feature_overview/mcp/index.md`
