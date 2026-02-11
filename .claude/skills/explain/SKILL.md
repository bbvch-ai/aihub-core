---
name: explain
description: Analyze and explain code in a specific folder or file. Reads
  documentation hierarchy, analyzes structure, identifies gaps, and provides
  comprehensive explanations. Can create missing READMEs.
allowed-tools: Read, Grep, Glob
---

# Explain Code - Understand and Document

Explain what's happening in a specific folder or file. Analyze code, read documentation, and create comprehensive
explanations.

## Process

1. Navigate to $ARGUMENTS (the folder or file to explain)
2. Read all existing README files hierarchically
3. Analyze the code structure and content
4. Identify documentation gaps
5. Create missing README files if needed
6. Provide a comprehensive explanation

## Step 1: Navigate and Survey

Explore the target location. Get an overview of the structure.

## Step 2: Read the Documentation Hierarchy

Follow the README-first documentation approach:

- Start with the project root README
- Check the scope-level README (if within a scope)
- Look for a README in the current directory
- Find all README files in subdirectories

## Step 3: Analyze the Code Structure

Examine the actual code to understand what's happening.

## Step 4: The Critical Analysis Questions

- **What is the primary purpose?** Problem solved, system fit, responsibilities.
- **What is the architecture?** Organization, main components/classes, dependencies.
- **What are the key workflows?** Data flow, entry points, usage patterns.
- **What's missing from documentation?** Missing READMEs, inaccurate docs, unclear sections.

## Step 5: Create Missing Documentation

Create README when: folder with multiple Python files but no README, complex component, standalone functionality.

Do NOT create when: folder has very few files, code is self-explanatory, docstrings are sufficient.

### Writing Style for READMEs

- Be VERY concise but complete
- Write for your future self
- Include "why" not just "what"
- DO NOT copy over code
- DO NOT include import/usage code blocks
- Talk on a high level about philosophy and approach

## Step 6: Provide Comprehensive Explanation

After analysis, provide an in-depth explanation to the user covering purpose, architecture, workflows, and any gaps found.
